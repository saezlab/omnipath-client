# omnipath-client

Python client for the OmniPath web services.

## Services

### OmniPath Database
Query protein interactions, annotations, complexes, and more from the
[OmniPath database](https://omnipathdb.org).

### OmniPath Utils
ID translation, taxonomy, orthology, and reference lists via the
[utils service](https://utils.omnipathdb.org).

## Quick Start

```bash
pip install omnipath-client
```

### ID Translation
```python
from omnipath_client.utils import map_name, translate_column

map_name('TP53', 'genesymbol', 'uniprot')
# {'P04637'}

# Translate DataFrame column (pandas, polars, or pyarrow)
translate_column(df, 'gene', 'genesymbol', 'uniprot')
```

### Taxonomy
```python
from omnipath_client.utils import ensure_ncbi_tax_id
ensure_ncbi_tax_id('human')  # 9606
```

### Orthology
```python
from omnipath_client.utils import orthology_translate
orthology_translate(['TP53'], source=9606, target=10090)
# {'TP53': {'Trp53'}}
```

### OmniPath Database
```python
import omnipath_client as op
df = op.interactions(entity_ids=['Q9Y6K9'])
```

## Getting started

- [Installation](installation.md) -- how to install the package
- [Quickstart](quickstart.md) -- basic usage examples
- [API Reference](reference/index.md) -- full API documentation
