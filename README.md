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

- Export **entities**, **interactions**, and **associations** (complexes,
  pathways, reactions) as DataFrames
- **Ontology** term lookup, search, and hierarchy trees
- Multi-backend output: [polars](https://pola.rs/) (default),
  [pandas](https://pandas.pydata.org/), or
  [pyarrow](https://arrow.apache.org/docs/python/)
- Optional graph conversion to [annnet](https://github.com/saezlab/annnet)
  objects
- Query validation against the API schema
- Caching via [download-manager](https://github.com/saezlab/download-manager)

## Installation

```bash
pip install omnipath-client
```

With polars (recommended default backend):

```bash
pip install omnipath-client polars
```

## Quick start

```python
import omnipath_client as op

# All interactions as a polars DataFrame
df = op.interactions()

# Directed interactions only
df = op.interactions(direction='directed')

# Human entities
df = op.entities(taxonomy_ids=['9606'])

# Interactions as an annnet graph
g = op.interactions(as_graph=True)

# Ontology term lookup
result = op.ontology_terms(['GO:0006915', 'MI:0326'])

# Choose a different backend
df = op.entities(backend='pandas')
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
