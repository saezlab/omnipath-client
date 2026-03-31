# Quickstart

This guide covers the basic usage of omnipath-client.

## Setup

```python
import omnipath_client as op
```

## Exporting data

### Entities

Entities include proteins, complexes, and other molecular species:

```python
# All entities
df = op.entities()

# Filter by organism (NCBI taxonomy ID 9606 = human)
df = op.entities(taxonomy_ids=['9606'])

# Filter by entity type
df = op.entities(entity_types=['protein'])
```

### Interactions

Interactions represent relationships between entities:

```python
# All interactions
df = op.interactions()

# Directed interactions only
df = op.interactions(direction='directed')

# Filter by sign (activation/inhibition)
df = op.interactions(sign='positive')

# Filter by source database
df = op.interactions(sources=['SIGNOR'])
```

### Associations

Associations represent membership in complexes, pathways, and reactions:

```python
# All associations
df = op.associations()

# Filter by parent entity type (e.g. complexes)
df = op.associations(parent_entity_types=['complex'])
```

## Choosing a DataFrame backend

By default, results are returned as
[polars](https://pola.rs/) DataFrames. You can choose a different backend:

```python
# pandas DataFrame
df = op.entities(backend='pandas')

# pyarrow Table
table = op.entities(backend='pyarrow')
```

To set the default backend for all queries, use the OO client:

```python
client = op.OmniPath(backend='pandas')
df = client.entities()
```

## Graph conversion

Interactions and associations can be returned as
[annnet](https://github.com/saezlab/annnet) graph objects:

```python
# Interactions as a graph
g = op.interactions(as_graph=True)

# Associations as a graph
g = op.associations(as_graph=True)
```

## Ontology endpoints

Look up ontology terms, search by name, or build hierarchy trees:

```python
# Batch term lookup
result = op.ontology_terms(['GO:0006915', 'MI:0326'])

# Search terms by name
result = op.search_terms(['apoptosis', 'kinase'])

# Get a merged hierarchy tree
tree = op.ontology_tree(['GO:0006915'])

# List available ontologies
ontologies = op.ontologies()
```

## Introspection

Explore available endpoints, parameters, and allowed values:

```python
client = op.OmniPath()

# All endpoints
client.endpoint_registry

# Parameters for an endpoint
client.params('exports/interactions/parquet')

# Allowed values for a parameter
client.values('exports/interactions/parquet', 'direction')
# ['any', 'directed', 'undirected']
```

## Custom API URL

To use a different API server (e.g. a local instance):

```python
client = op.OmniPath(base_url='http://localhost:8081')
df = client.interactions()
```
