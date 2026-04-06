# Working with OmniPath Utils

This vignette shows how to use the OmniPath Utils service for ID
translation, taxonomy resolution, orthology, and reference lists.

## Setup

```python
pip install omnipath-client
```

The utils module connects to `utils.omnipathdb.org` by default.
No database or local setup is needed.

```python
from omnipath_client.utils import (
    map_name,
    map_names,
    translate,
    translate_column,
    id_types,
    ensure_ncbi_tax_id,
    all_organisms,
    orthology_translate,
    get_reflist,
    is_swissprot,
)
```

## ID Translation

### Translate a single identifier

```python
# Gene symbol to UniProt
map_name('TP53', 'genesymbol', 'uniprot')
# {'P04637'}

# UniProt to gene symbol
map_name('P04637', 'uniprot', 'genesymbol')
# {'TP53'}

# UniProt to Entrez Gene ID
map_name('P04637', 'uniprot', 'entrez')
# {'7157'}
```

### Translate multiple identifiers

```python
# Returns union of all results
map_names(['TP53', 'EGFR', 'BRCA1'], 'genesymbol', 'uniprot')
# {'P04637', 'P00533', 'P38398'}

# Returns per-identifier results
translate(['TP53', 'EGFR', 'BRCA1'], 'genesymbol', 'uniprot')
# {'TP53': {'P04637'}, 'EGFR': {'P00533'}, 'BRCA1': {'P38398'}}
```

### Translate a DataFrame column

Works with pandas, polars, and pyarrow DataFrames:

```python
import pandas as pd

df = pd.DataFrame({
    'gene': ['TP53', 'EGFR', 'BRCA1', 'UNKNOWN'],
    'expression': [5.2, 3.1, 7.4, 0.1],
})

# Add UniProt column
result = translate_column(df, 'gene', 'genesymbol', 'uniprot')
#     gene  expression   uniprot
# 0   TP53         5.2   P04637
# 1   EGFR         3.1   P00533
# 2  BRCA1         7.4   P38398
# 3  UNKNOWN       0.1     None

# Drop rows without translation
result = translate_column(df, 'gene', 'genesymbol', 'uniprot',
                          keep_untranslated=False)

# No expansion (pick one if ambiguous)
result = translate_column(df, 'gene', 'genesymbol', 'uniprot',
                          expand=False)
```

### Available ID types

```python
types = id_types()
# [{'name': 'uniprot', 'label': 'UniProt AC', 'entity_type': 'protein', ...}, ...]
```

97 identifier types are supported, including proteins (UniProt, gene
symbols, Ensembl, Entrez, HGNC), small molecules (ChEBI, HMDB, PubChem,
DrugBank), and miRNA (miRBase).

### Controlling translation behavior

```python
# Skip special-case handling (direct lookup only)
map_name('tp53', 'genesymbol', 'uniprot', raw=True)
# set() — no case fallback in raw mode

# Force a specific backend
map_name('TP53', 'genesymbol', 'uniprot', backend='biomart')

# Translate for a different organism
map_name('Trp53', 'genesymbol', 'uniprot', ncbi_tax_id=10090)
```

## Taxonomy

### Resolve organism identifiers

```python
ensure_ncbi_tax_id('human')    # 9606
ensure_ncbi_tax_id('hsapiens') # 9606
ensure_ncbi_tax_id('hsa')      # 9606
ensure_ncbi_tax_id(10090)      # 10090

from omnipath_client.utils import ensure_common_name, ensure_latin_name
ensure_common_name(10090)       # 'mouse'
ensure_latin_name(9606)         # 'Homo sapiens'
```

### List all organisms

```python
organisms = all_organisms()
# [{'ncbi_tax_id': 9606, 'common_name': 'human', ...}, ...]
```

## Orthology

### Cross-species gene translation

```python
# Human to mouse orthologs
orthology_translate(['TP53', 'EGFR'], source=9606, target=10090)
# {'TP53': {'Trp53'}, 'EGFR': {'Egfr'}}

# With minimum supporting databases (HCOP)
orthology_translate(['TP53'], source=9606, target=10090, min_sources=5)

# Force a specific resource
orthology_translate(['TP53'], source=9606, target=10090, resource='oma')
```

### Translate DataFrame column to orthologs

```python
from omnipath_client.utils import orthology_translate_column

result = orthology_translate_column(
    df, 'gene', source=9606, target=10090,
)
```

## Reference Lists

### Check protein review status

```python
is_swissprot('P04637')   # True (TP53 is reviewed)
is_swissprot('A0A024R1R8')  # False (TrEMBL)

swissprots = get_reflist('swissprot', ncbi_tax_id=9606)
# set of all human SwissProt IDs
```

## Custom service URL

By default the client connects to `https://utils.omnipathdb.org`.
To use a local instance:

```python
from omnipath_client.utils._base import set_utils_url
set_utils_url('http://localhost:8083')
```
