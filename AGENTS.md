# AGENTS.md — omnipath-client Development Guide

## Project Overview

omnipath-client is the Python client for OmniPath web services:
1. **OmniPath Database** — protein interactions, annotations, complexes
   (served by omnipath-present at dev.omnipathdb.org)
2. **OmniPath Utils** — ID translation, taxonomy, orthology, reference lists
   (served by omnipath-utils at utils.omnipathdb.org)

**Key facts:**
- Python 3.10+, Hatchling build, BSD-3-Clause license
- PyPI: `pip install omnipath-client`
- The lightweight way for users to access OmniPath — no database setup needed

## Architecture

```
omnipath_client/
├── __init__.py        # Public API: OmniPath, entities, interactions, etc.
├── _client.py         # OmniPath class + module-level convenience functions
├── _query.py          # QueryBuilder for the database API
├── _inventory.py      # Auto-populated endpoint definitions from OpenAPI
├── _download.py       # Downloader (wraps dlmachine)
├── _response.py       # Response parsing (Parquet, JSON → DataFrame)
├── _graph.py          # DataFrame → annnet.Graph conversion
├── _endpoints.py      # EndpointDef + ParamDef dataclasses
├── _errors.py         # Exception hierarchy
├── _constants.py      # Base URLs, defaults
├── _types.py          # Type aliases
├── _session.py        # pkg_infra session
├── _metadata.py       # Version
└── utils/             # OmniPath Utils client
    ├── __init__.py    # Re-exports all utils functions
    ├── _base.py       # HTTP client (GET/POST to utils.omnipathdb.org)
    ├── _mapping.py    # ID translation: map_name, translate, translate_column
    ├── _taxonomy.py   # Taxonomy: ensure_ncbi_tax_id, resolve_organism
    ├── _orthology.py  # Orthology: translate, translate_column
    └── _reflists.py   # Reference lists: get_reflist, is_swissprot
```

## Utils module

The `utils` module mirrors the omnipath-utils Python API exactly:

```python
from omnipath_client.utils import (
    map_name, translate_column,  # ID translation
    ensure_ncbi_tax_id,          # Taxonomy
    orthology_translate,         # Orthology
    is_swissprot,                # Reference lists
    identify, all_mappings,      # Discovery
)
```

All functions make HTTP calls to utils.omnipathdb.org. DataFrame functions
use narwhals for pandas/polars/pyarrow support.

Custom URL: `from omnipath_client.utils._base import set_utils_url`

## Database API

```python
import omnipath_client as op
df = op.interactions(entity_ids = ['Q9Y6K9'])
df = op.entities(entity_types = ['protein'])
```

The database API auto-populates endpoint definitions from the server's
API schema (OpenAPI JSON or HTML parsing fallback), validates query
parameters, and delivers results as Parquet by default. Supports polars,
pandas, and pyarrow backends, and optional conversion to annnet Graph
objects.

## Dependencies
- `pkg-infra` — logging, config
- `dlmachine` — downloads + caching
- `narwhals` — DataFrame ops
- `requests` — HTTP (for utils module)

## Testing
```bash
uv sync
uv run pytest tests/ -v
```

55 tests, all use mocks (no live HTTP).
