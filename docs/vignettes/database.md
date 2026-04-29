# Querying the OmniPath Database

This vignette shows how to use omnipath-client to query the OmniPath
molecular biology database for relations, annotations, entity records,
and ontology terms.

## Setup

```bash
pip install omnipath-client
```

```python
import omnipath_client as op
```

## What's in the catalog?

```python
op.resources()
# [{'resource_id': 'bindingdb', ...}, {'resource_id': 'foodb', ...}, ...]
```

## One-call queries with `lookup()` and `related()`

For most analysis questions you only need these two helpers. They
auto-resolve free-text inputs, fetch the matching tables, and pivot
the requested identifiers into named columns.

### Resolve and enrich

```python
# Free-text query → entity records with the IDs you ask for
op.lookup(
    ['caffeine', 'metformin', 'TP53'],
    id_types=['name', 'chebi', 'hmdb', 'uniprot', 'genesymbol'],
)
```

### Joined relations

```python
# Drug targets for caffeine — positional arg matches either side
op.related(
    'caffeine',
    sources=['bindingdb'],
    id_types=['name', 'uniprot', 'genesymbol'],
)

# Pin direction with subject= or object=
op.related(
    object=['WP253', 'R-HSA-70171'],
    sources=['wikipathways', 'reactome'],
    relation_categories=['annotation'],
    id_types=['name', 'uniprot', 'chebi'],
    group_by='object_name',
)

# Filter participants by friendly type alias
op.related(
    'metformin',
    sources=['signor'],
    participant_types=['protein'],
)
```

## Lower-level primitives

When the wrappers don't fit, use the export endpoints directly.

### Entities

```python
# All human entities
df = op.entities(taxonomy_ids=['9606'])

# Filter by source
df = op.entities(sources=['hmdb'])

# Lookup by primary key
df = op.entities(entity_pks=['1568012', '8584'])
```

### Relations

```python
# All relations from one source
df = op.relations(sources=['signor'])

# Relations involving a specific entity_pk
df = op.relations(entity_pks=['2119890'])         # either side
df = op.relations(subject_entity_pks=['2401277']) # outgoing
df = op.relations(object_entity_pks=['2233186'])  # incoming

# Filter by predicate or category
df = op.relations(predicates=['interacts_with'])
df = op.relations(relation_categories=['membership'])
```

### Annotations

```python
df = op.annotations(prefixes=['chebi'])
```

### Free-text resolution and paged slices

```python
# Resolve names/aliases to entity_pks
op.resolve(['caffeine', 'TP53', 'WP253'])

# Page through entities with a free-text query
op.entities_slice(query='glucose', limit=20)
```

## Ontology

```python
# Look up ontology terms by ID
df = op.ontology_terms(['GO:0006915', 'GO:0012501'])

# Search ontology terms by name across ontologies
op.search_terms(['glycolysis', 'apoptosis'])

# Hierarchy tree
tree = op.ontology_tree(['GO:0006915'])
```

## Backends

By default, results are returned as polars DataFrames. You can choose
pandas or pyarrow:

```python
client = op.OmniPath(backend='pandas')
df = client.relations(sources=['signor'])
# Returns pandas DataFrame
```

## Cache control

```python
# First-touch refresh inside the block; subsequent identical
# requests within the same block hit the freshly cached entry
with op.fresh():
    df = op.related('caffeine', sources=['bindingdb'])

# Wipe the on-disk cache (incl. the OpenAPI spec)
op.cache_clear()
```

## Custom server

```python
client = op.OmniPath(base_url='http://localhost:8082/api')
```

## Further resources

- [OmniPath web service](https://omnipathdb.org)
- [Interactive explorer](https://explore.omnipathdb.org)
- [OmnipathR (R client)](https://r.omnipathdb.org)
