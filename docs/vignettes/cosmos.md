# COSMOS Prior-Knowledge Network

This vignette shows how to use omnipath-client to access the COSMOS
prior-knowledge network (PKN) -- a multi-layer network designed for
multi-omics causal reasoning with
[cosmosR](https://github.com/saezlab/cosmosR).

The COSMOS PKN integrates metabolite-protein interactions, protein-protein
signaling, and gene regulation from curated databases into a single
directed signed network. It is served by the
[metabo.omnipathdb.org](https://metabo.omnipathdb.org) web service and
built by the [omnipath-metabo](https://github.com/saezlab/omnipath-metabo)
package.

## Setup

```python
pip install omnipath-client
```

```python
import omnipath_client as oc
```

## Network categories

The PKN is organized into six categories covering different layers of
molecular interaction:

| Category | Description |
|----------|-------------|
| `transporters` | Metabolite transport across membranes (TCDB, SLC, GEMs, MRCLinksDB) |
| `receptors` | Metabolite-receptor binding at the cell surface (STITCH, MRCLinksDB) |
| `allosteric` | Allosteric regulation of enzymes by metabolites (BRENDA, STITCH) |
| `enzyme_metabolite` | Enzyme-metabolite stoichiometric reactions from GEMs |
| `ppi` | Protein-protein signaling from OmniPath |
| `grn` | Gene regulatory network from CollecTRI / DoRothEA |

## Fetch the full PKN

```python
# Full human PKN (all 6 categories)
df = oc.cosmos.get_pkn('human')
```

The result is a DataFrame with columns `source`, `target`, and `sign`
(mode of regulation: 1 = stimulation, -1 = inhibition).

## Filter by category

```python
# Only transporters and receptors
df = oc.cosmos.get_pkn('human', categories=['transporters', 'receptors'])

# PPI layer only
df = oc.cosmos.get_pkn('human', categories='ppi')
```

## Filter by resource

```python
# Only STITCH receptor edges
df = oc.cosmos.get_pkn(
    'human',
    categories='receptors',
    resources='STITCH',
)
```

## Multi-organism support

The PKN is available for human, mouse, and rat. The `organism` parameter
accepts NCBI taxonomy IDs, common names, Latin names, or short codes.

```python
# Mouse PKN
df_mouse = oc.cosmos.get_pkn('mouse')

# Rat PKN
df_rat = oc.cosmos.get_pkn('rat')

# Using NCBI taxonomy ID
df = oc.cosmos.get_pkn(10090)
```

## AnnNet graph conversion

Convert the PKN to an [AnnNet](https://github.com/saezlab/annnet)
graph object for network analysis:

```python
# Directly as an AnnNet graph
g = oc.cosmos.get_pkn('mouse', format='annnet')

# Or convert an existing DataFrame
df = oc.cosmos.get_pkn('human')
g = oc.cosmos.to_annnet(df)
```

## Convenience functions

Explore what is available on the server:

```python
# Available categories
oc.cosmos.categories()
# ['transporters', 'receptors', 'allosteric', 'enzyme_metabolite', 'ppi', 'grn']

# Supported organisms
oc.cosmos.organisms()
# [9606, 10090, 10116]

# Resources per category
oc.cosmos.resources()
# {'transporters': ['TCDB', 'SLC', 'GEM:Human-GEM', ...], ...}
```

## Web service

The COSMOS PKN is served at
[metabo.omnipathdb.org](https://metabo.omnipathdb.org). You can also
query the REST API directly:

```
GET https://metabo.omnipathdb.org/cosmos/pkn?organism=9606&categories=all
GET https://metabo.omnipathdb.org/cosmos/pkn?organism=10090&categories=transporters,ppi
GET https://metabo.omnipathdb.org/cosmos/categories
GET https://metabo.omnipathdb.org/cosmos/organisms
GET https://metabo.omnipathdb.org/cosmos/resources
```
