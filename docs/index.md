<div class="sv-hero">
<div class="sv-hero-grid">
  <img class="sv-hero-logo" src="assets/omnipath-logo.svg" alt="OmniPath logo">
  <div class="sv-hero-text">
  <div class="sv-kicker">Python client for OmniPath</div>
  <h1>omnipath-client</h1>
  <p class="sv-lead">
    omnipath-client gives Python access to OmniPath, prior knowledge on
    molecular biology integrated from more than 200 resources: interactions,
    networks, annotations and complexes of proteins, genes and metabolites. It
    also translates identifiers between databases and organisms, and fetches
    the COSMOS network for multi-omics analysis. Results come as polars, pandas
    or pyarrow data frames.
  </p>
  </div>
</div>
</div>

## What you can access

OmniPath runs as three web services. The client has one part for each:

| Service | What it provides | In the client |
| --- | --- | --- |
| [OmniPath database](https://dev.omnipathdb.org) | Molecules and their identifiers, interactions, annotations and complexes from 200+ resources; named network datasets such as LIANA (ligand–receptor) and MetaLinksDB (metabolite–protein) | `op.lookup()`, `op.datasets` |
| [OmniPath Utils](https://utils.omnipathdb.org) | Identifier translation for more than 100 identifier types, taxonomy, orthology, reference lists | `op.utils` |
| [OmniPath Metabo](https://metabo.omnipathdb.org) | The COSMOS prior-knowledge network: signaling, gene regulation, metabolite–protein and metabolic reactions | `op.cosmos` |

No local database is necessary: the client queries the services and keeps a
cache of the responses.

## Get started

### 1. Install

```bash
pip install "omnipath-client[polars]"
```

This installs the client with polars, its default data frame backend. For the
pandas and pyarrow backends and installation from source, see
[Installation](installation.md).

### 2. Try it

**Translate identifiers** with OmniPath Utils:

```python
from omnipath_client.utils import map_name, translation_df

map_name('TP53', 'genesymbol', 'uniprot')     # {'P04637'}
map_name('caffeine', 'name', 'chebi')         # {'CHEBI:27732'}

translation_df('genesymbol', 'uniprot')       # the full table, 165k rows
```

**Look up molecules** in the OmniPath database, with the identifiers you
want as columns. The result has one row for each matching entity:

```python
import omnipath_client as op

op.lookup('caffeine', id_types = ['name', 'chebi', 'hmdb', 'inchikey'])
```

**Get a network dataset** as a data frame. The datasets are new, and for now
a preview deployment serves them:

```python
op.set_base_url('https://dev3.omnipathdb.org/api')

op.datasets.names()                     # ['metalinksdb', 'liana']
op.datasets.liana.get(limit = 5)        # ligand-receptor interactions
```

**Fetch the COSMOS network**, here only its metabolite–receptor part:

```python
op.cosmos.get_pkn('human', categories = ['receptors'])   # 10.9k interactions
```

The [Quickstart](quickstart.md) explains these calls and their options.

### 3. Learn more

- **Vignettes**:
  [OmniPath Utils](vignettes/utils.md) (identifiers, taxonomy, orthology) ·
  [OmniPath database](vignettes/database.md) ·
  [network datasets](vignettes/datasets.md) ·
  [COSMOS PKN](vignettes/cosmos.md)
- **[API reference](reference/index.md)**: all functions and their options
- **[About](about.md)**: license, citation and contact

## Why use OmniPath?

OmniPath combines more than 200 resources into one consistent collection:
protein–protein and gene regulatory interactions, enzyme–substrate
relationships, protein complexes, functional annotations, intercellular
communication, and metabolite networks. You query one service instead of
dozens of databases, each with its own format and identifiers.

The client is free to use in any project under the BSD-3-Clause license.

<div class="sv-ecosystem">
  <a href="https://sysbioverse.org/"><img src="assets/sysbioverse-logo.svg" alt="sysbioverse logo"></a>
  <p>
    omnipath-client is part of <a href="https://sysbioverse.org/">sysbioverse</a>, an
    ecosystem of free open source packages for molecular systems biology. The
    packages share data structures, design principles and workflows, and build
    on the <a href="https://scverse.org/">scverse</a> ecosystem for single-cell
    omics analysis.
  </p>
</div>
