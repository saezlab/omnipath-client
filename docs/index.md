# omnipath-client

Python client for the [OmniPath](https://omnipathdb.org/) molecular biology
prior-knowledge web API.

omnipath-client provides validated, cache-aware access to the OmniPath API,
delivering results as [polars](https://pola.rs/),
[pandas](https://pandas.pydata.org/), or
[pyarrow](https://arrow.apache.org/docs/python/) DataFrames. Network data
can optionally be returned as [annnet](https://github.com/saezlab/annnet)
graph objects.

## Features

- **Export endpoints** for entities, interactions, and associations (complexes,
  pathways, reactions)
- **Ontology endpoints** for term lookup, search, and hierarchy trees
- **Multi-backend** DataFrame output: polars (default), pandas, pyarrow
- **Query validation** against the API schema (endpoint names, parameter names,
  enum values)
- **Caching** of downloaded data via
  [download-manager](https://github.com/saezlab/download-manager)
- **Graph conversion** to [annnet](https://github.com/saezlab/annnet) objects
  for network data

## Quick example

```python
import omnipath_client as op

# Get all interactions as a polars DataFrame
df = op.interactions()

# Filter by direction
df = op.interactions(direction='directed')

# Get entities for a specific organism
df = op.entities(taxonomy_ids=['9606'])

# Return interactions as an annnet graph
g = op.interactions(as_graph=True)
```

## Getting started

- [Installation](installation.md) -- how to install the package
- [Quickstart](quickstart.md) -- basic usage examples
- [API Reference](reference/index.md) -- full API documentation
