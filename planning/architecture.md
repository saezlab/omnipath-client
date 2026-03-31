# OmniPath Client — Architecture Plan

## Context

New Python client for the OmniPath molecular biology web API
(`https://dev.omnipathdb.org/`), replacing the old `omnipath` package. The API
currently serves Parquet data via POST endpoints, but the client must be
designed to accommodate other formats and endpoints in the future. The client
must provide validated queries, multi-backend DataFrame output, graph
conversion, and self-updating endpoint introspection.

## Module Structure

```
omnipath_client/
    __init__.py          # Re-exports public API from _client; triggers inventory load
    _metadata.py         # (exists) version, author
    _client.py           # OmniPath class + module-level convenience functions
    _session.py          # Session via pkg_infra (get_session, config, logging)
    _constants.py        # Base URL, static fallback inventory, defaults
    _types.py            # BackendType literal, enums, type aliases
    _inventory.py        # Fetch + parse API schema -> endpoint registry
    _endpoints.py        # EndpointDef + ParamDef dataclasses
    _query.py            # QueryBuilder + Query (validation against inventory)
    _download.py         # Downloader wrapping download-manager (async-capable)
    _response.py         # Response dispatch: Parquet, JSON, etc. + backend conversion
    _graph.py            # DataFrame -> annnet.Graph conversion
    _errors.py           # Exception hierarchy
```

## Data Flow

```
op.interactions(entity_ids=['Q9Y6K9'])
  -> OmniPath (lazy singleton or explicit)
  -> Inventory (loaded at import, non-blocking on failure)
  -> QueryBuilder.build() — validate endpoint, params, values
  -> Query object
  -> Downloader.fetch(query) — async POST via download-manager (cache-aware)
  -> Path to cached response file (.parquet, .json, etc.)
  -> ResponseHandler.parse(path, format, backend) — dispatch by format
  -> polars/pandas/pyarrow DataFrame
  -> (optional) interactions_to_graph(df) -> annnet.Graph
```

## Key Components

### 1. Public API (`_client.py`)

Two interfaces: OO client for control, module-level functions for convenience.

```python
# OO
client = op.OmniPath(backend='pandas', base_url='...')
df = client.interactions(entity_ids=['Q9Y6K9'])

# Convenience (lazy default singleton)
df = op.interactions(entity_ids=['Q9Y6K9'])
g = op.interactions(as_graph=True, entity_ids=['Q9Y6K9'])

# Introspection
client.endpoints
client.params('exports/interactions')
client.values('exports/entities', 'entity_types')
```

Methods mirror the 6 API endpoints:
- `entities(**filters)`, `interactions(**filters)`, `associations(**filters)`
- `entity_lookup(identifiers)`, `ontology_terms(term_ids)`,
  `ontology_tree(term_ids)`

`interactions()` and `associations()` accept `as_graph=True` to return
`annnet.Graph`.

### 2. Inventory (`_inventory.py`)

Auto-populates endpoint/param/value definitions at **import time**.

**Phase 1 (now):** Parse the rendered HTML from `/api-docs` to extract
endpoints, parameters, and allowed values. Runs at import time but **failure
must not block import** — on any error (network, parse), log a warning and
fall back to static definitions in `_constants.py`.

**Phase 2 (soon):** When the standard FastAPI/Swagger `openapi.json` becomes
available (the server already supports it locally via
`GET /openapi.json`), switch to fetching and parsing that. Same
load-at-import + silent-fallback pattern.

Both phases share:
1. Check for cached inventory (via cache-manager, with TTL).
2. Attempt to fetch and parse the API schema.
3. On failure, fall back to static definitions in `_constants.py`.
4. Expose: `endpoints()`, `params(endpoint)`, `allowed_values(endpoint,
   param)`.

### 3. Query Validation (`_query.py`)

`QueryBuilder.build(endpoint, **params)` validates against inventory:
- Endpoint exists
- Param names recognized
- Param types correct (string[], string, bool, enum)
- Values in allowed set (if constrained)
- Required params present

Raises specific exceptions from `_errors.py`.

### 4. Downloads (`_download.py`)

Wraps `download_manager.DownloadManager` with **async support as a goal**:
- POST with JSON body (the API uses POST endpoints)
- Cache keyed on URL + body
- Returns path to cached response file

**Async strategy:** download-manager currently uses synchronous
requests/pycurl backends. Plan:
1. Add an async backend to download-manager (e.g. `httpx.AsyncClient`).
2. Update cache-manager for async-compatible file I/O where needed.
3. Expose both sync and async interfaces in omnipath-client:
   `client.interactions()` (sync) and `await client.ainteractions()` or an
   async context manager.
4. Initial implementation is sync-first; async added incrementally to
   download-manager and cache-manager.

### 5. Response Handling (`_response.py`)

**Format-agnostic dispatch** — designed to accommodate future response formats:

```python
def parse_response(
    source: Path | BytesIO,
    format: str = 'parquet',   # future: 'json', 'csv', 'arrow_ipc', ...
    backend: BackendType = 'polars',
) -> Any:
```

- **Parquet** (current default): read via `pyarrow.parquet.read_table()`,
  convert to backend.
- **Future formats**: JSON, CSV, Arrow IPC, etc. — each gets a reader
  function, dispatched by `format`.
- Default backend: **polars** (Arrow-native, fast, matches annnet's Polars
  backend).
- narwhals used as compatibility bridge for DataFrame operations.
- The `format` is determined from the endpoint definition in the inventory, so
  adding a new format only requires a reader function and updating the
  endpoint metadata.

### 6. Graph Conversion (`_graph.py`)

For interactions: map `member_a_id`/`member_b_id` to source/target edges,
create `annnet.Graph`. For associations: parent-member relationships as
hyperedges.

### 7. Error Hierarchy (`_errors.py`)

```
OmniPathError
  +-- OmniPathAPIError (HTTP 4xx/5xx)
  +-- OmniPathConnectionError
  +-- ValidationError
  |     +-- UnknownEndpointError
  |     +-- UnknownParameterError
  |     +-- InvalidParameterValueError
  |     +-- MissingParameterError
  +-- BackendNotAvailableError
```

### 8. Config, Logging & Session (`_session.py`)

**All configuration and logging uses pkg_infra (`saezlab_core`).**

- **Config**: `saezlab_core.config.ConfigLoader.load_config()` provides
  hierarchical OmegaConf/YAML config merged from: ecosystem -> package
  defaults -> user dir -> workdir -> env vars. omnipath-client ships a
  `default_settings.yaml` (bundled as package data under
  `omnipath_client/data/`) with its own settings under a dedicated section
  (e.g. `omnipath_client:` with keys `base_url`, `backend`, `cache_ttl`,
  `timeout`, `retries`).

- **Logging**: `saezlab_core.logger.configure_loggers_from_omegaconf()` +
  standard `logging.getLogger(__name__)` in each module. Logging config lives
  in the same YAML hierarchy.

- **Session**: `saezlab_core.session.get_session()` singleton ties config +
  logger + runtime metadata. The client calls this once at initialization.

**pkg_infra considerations**: The current `Settings` schema in
`saezlab_core.schema` uses `extra="forbid"` on all models. For
omnipath-client to add its own config section, the schema needs to either:
(a) allow extra fields at the top level, or (b) support a generic
plugin/package config namespace. This is an upstream change to pkg_infra that
should be designed to work for all saezlab client packages, not just
omnipath-client.

Similarly, `ConfigLoader.read_package_default()` currently reads from
`saezlab_core.data` — it needs to be parameterized to also read defaults
from the calling package's data directory. This upstream generalization
benefits all packages using pkg_infra.

## Cross-cutting: Upstream Work Required

| Package              | Work needed                                              |
|----------------------|----------------------------------------------------------|
| **pkg_infra**        | Generalize config schema for per-package sections;       |
|                      | parameterize `read_package_default()` for caller package;|
|                      | evaluate session API for client-library use              |
| **download-manager** | Add async download backend (httpx); ensure POST+JSON     |
|                      | support                                                  |
| **cache-manager**    | Async-compatible file I/O if needed by async download    |

## Testing Strategy

- **Unit tests**: mock inventory, query validation, response conversion, graph
  conversion
- **Integration tests**: mock HTTP server returning sample Parquet, full
  round-trip; also tests against local server
  (`uv run uvicorn api_service.main:app --port 8081`)
- **Fixtures**: pre-generated small Parquet files, mock DownloadManager

## Implementation Order

1. `_errors.py`, `_types.py`, `_constants.py` — foundations
2. `_endpoints.py` — dataclasses for endpoint/param definitions
3. `_session.py` — integrate pkg_infra config/logging/session (upstream
   updates to pkg_infra as needed)
4. `_inventory.py` — HTML parsing now, `openapi.json` soon; load at import,
   fail silently
5. `_query.py` — query builder with validation
6. `_download.py` — sync wrapper first; async in download-manager as follow-up
7. `_response.py` — Parquet reader first, format dispatch for future
   extensibility
8. `_graph.py` — annnet conversion
9. `_client.py` — orchestrator + public API
10. `__init__.py` — re-exports + import-time inventory load
11. Tests throughout
