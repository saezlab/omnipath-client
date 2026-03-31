# OmniPath Client — Instructions for AI Assistants

You are working on `omnipath-client`, the new Python client for the OmniPath
molecular biology prior-knowledge web API.

## Architecture plan

Read `planning/architecture.md` for the full architecture plan: module
structure, data flow, component descriptions, and implementation order.
The initial specifications are in `planning/initial_specs.md`.

## The web API

- **Production**: https://dev.omnipathdb.org/
- **API docs** (rendered): https://dev.omnipathdb.org/api-docs
- **Server repo**: https://github.com/saezlab/omnipath-present
- **Run locally**:
  ```
  git clone git@github.com:saezlab/omnipath-present.git
  cd omnipath-present/api-service
  uv sync
  uv run uvicorn api_service.main:app --reload --port 8081
  curl http://localhost:8081/openapi.json
  ```

The API uses POST endpoints returning Parquet files. A standard
`openapi.json` will be available soon; until then the HTML API docs page
is the reference.

## Related local repositories

| Package | Local path | Purpose |
|---------|-----------|---------|
| **saezverse** | `/home/denes/saezverse/` | Architecture repo: coding conventions, package descriptions, ADRs, plans |
| **pkg_infra** (saezlab_core) | `/home/denes/pypath-new/pkg_infra/` | Config, logging, and session infrastructure for all saezlab packages |
| **download-manager** | — | Cache-aware download manager ([GitHub](https://github.com/saezlab/download-manager)) |
| **cache-manager** | — | SQLite-backed file caching ([GitHub](https://github.com/saezlab/cache-manager)) |
| **annnet** | — | Annotated network/graph library, Polars-backed ([GitHub](https://github.com/saezlab/annnet)) |
| **omnipath** (old client) | — | Legacy Python client being replaced ([GitHub](https://github.com/saezlab/omnipath)) |

## Key dependencies

- **pkg_infra (`saezlab_core`)** — all config, logging, and session management
  must go through this package. Source at
  `/home/denes/pypath-new/pkg_infra/saezlab_core/`. Uses OmegaConf YAML
  hierarchy for config, Python `dictConfig` for logging, and a singleton
  `Session` object. If it lacks features needed by this client, contribute
  upstream rather than building parallel solutions.
- **download-manager** — wraps HTTP downloads with cache-manager integration.
  Async support is a goal (not yet implemented).
- **narwhals** — dataframe compatibility layer. Default backend is **polars**.
- **annnet** — for converting interaction/association data to graph objects.

## Coding conventions

Follow the saezlab Python coding style documented in
`/home/denes/saezverse/human/guidelines/python-coding-style.md`. Key points:

- Spaces around `=` in keyword arguments and default values
- Blank lines inside functions before/after blocks and between logical segments
- Argument lists on multiple lines: opening paren on first line, each arg on
  its own line, trailing comma, closing paren at original indentation
- Single quotes for strings
- Google (Napoleon) docstring style with triple quotes on separate lines
- Resource names as single words without underscores

## Package description

The saezverse package description for this client is at
`/home/denes/saezverse/human/packages/omnipath-client.md`.
