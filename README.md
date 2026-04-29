# omnipath-client

[![Tests](https://img.shields.io/github/actions/workflow/status/saezlab/omnipath-client/ci-testing-unit.yml?branch=master&label=tests)](https://github.com/saezlab/omnipath-client/actions/workflows/ci-testing-unit.yml)
[![Codecov](https://img.shields.io/codecov/c/github/saezlab/omnipath-client)](https://codecov.io/gh/saezlab/omnipath-client)
[![Docs](https://img.shields.io/badge/docs-MkDocs-blue)](https://saezlab.github.io/omnipath-client/)
[![PyPI](https://img.shields.io/pypi/v/omnipath-client)](https://pypi.org/project/omnipath-client/)
[![Python](https://img.shields.io/pypi/pyversions/omnipath-client)](https://pypi.org/project/omnipath-client/)
[![License](https://img.shields.io/github/license/saezlab/omnipath-client)](https://github.com/saezlab/omnipath-client/blob/master/LICENSE)

Python client for the [OmniPath](https://omnipathdb.org/) molecular biology
prior-knowledge web API.

## Features

- One-call **`lookup()`** and **`related()`** helpers that resolve
  free-text queries, fetch the matching entities/relations, and pivot
  identifiers into named columns — no manual primary-key juggling
- Friendly id-type aliases (`name`, `chebi`, `hmdb`, `uniprot`,
  `genesymbol`, `kegg`, …) and participant-type aliases
  (`protein`, `small_molecule`, …) that hide the MI/OM ontology codes
- Lower-level primitives: export **entities**, **relations**, and
  **annotations** as DataFrames; resolve free-text identifiers; slice
  with paging
- **Ontology** term lookup, search, and hierarchy trees
- Multi-backend output: [polars](https://pola.rs/) (default),
  [pandas](https://pandas.pydata.org/), or
  [pyarrow](https://arrow.apache.org/docs/python/)
- Optional graph conversion to [annnet](https://github.com/saezlab/annnet)
  objects
- Query validation against the API schema
- Caching via [download-manager](https://github.com/saezlab/download-manager),
  with a `fresh()` context manager for first-touch refresh

## Installation

```bash
pip install omnipath-client
```

With polars (recommended default backend):

```bash
pip install omnipath-client polars
```

## Quick start

The two high-level helpers, `lookup()` and `related()`, cover most use
cases in a single call:

```python
import omnipath_client as op

# Resolve names and pivot identifiers into named columns
op.lookup(
    ['caffeine', 'metformin', 'TP53'],
    id_types=['name', 'chebi', 'hmdb', 'uniprot', 'genesymbol'],
)

# Compounds reported in strawberry (FooDB), as a wide joined table
op.related(
    subject='Strawberry',
    sources=['foodb'],
    id_types=['name', 'chebi', 'hmdb'],
)

# Drug targets for caffeine (positional arg matches either side)
op.related(
    'caffeine',
    sources=['bindingdb'],
    id_types=['name', 'uniprot', 'genesymbol'],
)

# Pathway members from WikiPathways and Reactome at once
op.related(
    object=['WP253', 'R-HSA-70171'],
    sources=['wikipathways', 'reactome'],
    relation_categories=['annotation'],
    id_types=['name', 'uniprot', 'chebi'],
    group_by='object_name',
)
```

The lower-level primitives are still available for paged scans, raw
parquet, or graph export:

```python
# All relations as a polars DataFrame
df = op.relations()

# Resolve free-text identifiers to entity primary keys
op.resolve(['caffeine', 'TP53'])

# Human entities
df = op.entities(taxonomy_ids=['9606'])

# Relations as an annnet graph
g = op.relations(as_graph=True)

# Ontology term lookup
result = op.ontology_terms(['GO:0006915', 'MI:0326'])

# Choose a different backend
df = op.entities(backend='pandas')
```

Cache control:

```python
# Force a one-shot refresh for everything touched in the block
with op.fresh():
    df = op.related('caffeine', sources=['bindingdb'])

# Wipe the entire on-disk cache (e.g. after a server redeploy)
op.cache_clear()
```

For more examples, see the [quickstart guide](https://saezlab.github.io/omnipath-client/quickstart/).

## OmniPath Utils

The client provides access to the [OmniPath Utils](https://utils.omnipathdb.org)
service for ID translation, taxonomy, and orthology:

```python
from omnipath_client.utils import (
    map_name,           # translate identifiers
    translate_column,   # translate DataFrame columns
    ensure_ncbi_tax_id, # resolve organism names
    orthology_translate, # cross-species translation
)

# Gene symbol to UniProt
map_name('TP53', 'genesymbol', 'uniprot')  # {'P04637'}

# Organism resolution
ensure_ncbi_tax_id('mouse')  # 10090

# Cross-species translation
orthology_translate(['TP53'], source=9606, target=10090)
# {'TP53': {'Trp53'}}
```

Full API: [utils.omnipathdb.org](https://utils.omnipathdb.org)

## Documentation

Full documentation: [saezlab.github.io/omnipath-client](https://saezlab.github.io/omnipath-client/)

## Data licensing

The data served by OmniPath is combined from many original resources, each
with their own license terms. The OmniPath client software is BSD-3-Clause,
but the **data** is subject to the licenses of the original sources. Some
resources restrict commercial use. Tools and documentation for managing
license-based access control will be provided in a future release.

## Citation

If you use OmniPath in your research, please cite:

> Türei D, Schaul J, Palacio-Escat N, Bohár B, Bai Y, Ceccarelli F,
> Çevrim E, Daley M, Darcan M, Dimitrov D, Doğan T, Domingo-Fernández D,
> Dugourd A, Gábor A, Gul L, Hall BA, Hoyt CT, Ivanova O, Klein M,
> Lawrence T, Mañanes D, Módos D, Müller-Dott S, Ölbei M, Schmidt C,
> Şen B, Theis FJ, Ünlü A, Ulusoy E, Valdeolivas A, Korcsmáros T,
> Saez-Rodriguez J. (2026) OmniPath: integrated knowledgebase for
> multi-omics analysis. *Nucleic Acids Research* 54(D1):D652-D660.
> [doi:10.1093/nar/gkaf1126](https://doi.org/10.1093/nar/gkaf1126)

## License

The client software is licensed under
[BSD-3-Clause](https://github.com/saezlab/omnipath-client/blob/master/LICENSE).
See [Data licensing](#data-licensing) above for information about the data.
