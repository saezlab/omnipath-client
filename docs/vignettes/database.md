# Querying the OmniPath Database

This vignette shows how to use omnipath-client to query the OmniPath
molecular biology database for interactions, annotations, complexes,
and more.

## Setup

```python
pip install omnipath-client
```

```python
import omnipath_client as op
```

## Protein interactions

```python
# All post-translational interactions for specific proteins
df = op.interactions(entity_ids=['Q9Y6K9', 'P04637'])

# All interactions (large dataset)
df = op.interactions()
```

## Entity lookup

```python
# Look up entities by ID
df = op.entities(entity_ids=['TP53', 'EGFR', 'BRCA1'])

# Filter by type
df = op.entities(entity_types=['protein'], taxonomy_ids=['9606'])
```

## Associations

```python
# Protein complexes
df = op.associations(parent_entity_types=['complex'])
```

## Ontology

```python
# Gene Ontology terms
df = op.ontology_terms(['GO:0006915', 'GO:0012501'])

# Ontology tree
tree = op.ontology_tree(['GO:0006915'])
```

## Backends

By default, results are returned as polars DataFrames. You can choose
pandas or pyarrow:

```python
client = op.OmniPath(backend='pandas')
df = client.interactions(entity_ids=['Q9Y6K9'])
# Returns pandas DataFrame
```

## Custom server

```python
client = op.OmniPath(base_url='http://localhost:8082/api')
```

## Further resources

- [OmniPath web service](https://omnipathdb.org)
- [Interactive explorer](https://explore.omnipathdb.org)
- [OmnipathR (R client)](https://r.omnipathdb.org)
