# omnipath-client

**The easiest way to access molecular biology knowledge in Python.**

omnipath-client connects you to the [OmniPath](https://omnipathdb.org)
ecosystem -- a comprehensive collection of molecular biology databases
covering signaling, gene regulation, protein interactions, metabolomics,
and more.

## Why OmniPath?

OmniPath integrates data from **200+ databases** into a unified resource:
protein-protein interactions, enzyme-substrate relationships, transcription
factor targets, protein complexes, functional annotations, intercellular
communication, and metabolite networks. Instead of querying dozens of
databases individually, query OmniPath once.

## Why this client?

- **No setup needed** -- queries the web service, no local database required
- **97 identifier types** -- translate between UniProt, gene symbols, Ensembl,
  ChEBI, HMDB, and 90+ other ID systems
- **28,000 organisms** -- taxonomy resolution across NCBI, Ensembl, KEGG, OMA
- **Orthology** -- cross-species gene translation with 6 backends
- **DataFrames** -- returns polars, pandas, or pyarrow DataFrames
- **BSD-3-Clause** -- free to use in any project

## Quick examples

### Translate gene symbols to UniProt

```python
from omnipath_client.utils import map_name, translation_df

map_name('TP53', 'genesymbol', 'uniprot')
# {'P04637'}

# Full translation table as DataFrame
df = translation_df('genesymbol', 'uniprot')
```

### Cross-species translation

```python
from omnipath_client.utils import orthology_translate

orthology_translate(['TP53', 'EGFR'], source=9606, target=10090)
# {'TP53': {'Trp53'}, 'EGFR': {'Egfr'}}
```

### Query protein interactions

```python
import omnipath_client as op

# One-call helper: caffeine drug targets with UniProt + gene symbols
op.related(
    'caffeine',
    sources=['bindingdb'],
    id_types=['name', 'uniprot', 'genesymbol'],
)

# Or the lower-level primitive
df = op.relations(entity_pks=['2119890'])
```

### Resolve and enrich identifiers

```python
op.lookup(
    ['caffeine', 'metformin', 'TP53'],
    id_types=['name', 'chebi', 'hmdb', 'uniprot', 'genesymbol'],
)
```

### Explore the API

```python
import omnipath_client as op

op.endpoints()                                       # all endpoints
op.params('exports/relations/parquet')                # available filters
op.values('exports/entities/parquet', 'entity_types') # allowed values
op.resources()                                        # source catalog
```

## Learn more

- **[OmniPath Utils vignette](vignettes/utils.md)** -- ID translation,
  taxonomy, orthology, reference lists
- **[OmniPath Database vignette](vignettes/database.md)** -- interactions,
  annotations, complexes
- **[COSMOS PKN vignette](vignettes/cosmos.md)** -- multi-layer
  prior-knowledge network for multi-omics causal reasoning
- **[API Reference](reference/index.md)** -- full function documentation
- **[Installation](installation.md)** -- setup instructions

## Services

| Service | URL | What it provides |
|---------|-----|-----------------|
| OmniPath Database | [dev.omnipathdb.org](https://dev.omnipathdb.org) | Interactions, annotations, complexes, ontology |
| OmniPath Utils | [utils.omnipathdb.org](https://utils.omnipathdb.org) | ID translation, taxonomy, orthology, reference lists |
| OmniPath Metabo | [metabo.omnipathdb.org](https://metabo.omnipathdb.org) | COSMOS PKN, metabolite-protein interactions |
