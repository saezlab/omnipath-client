# Quickstart

This guide covers the basic usage of omnipath-client.

## Setup

```python
import omnipath_client as op
```

## High-level helpers

Two helpers, `lookup()` and `related()`, fold the common
*resolve → fetch → join* pattern into a single call. They accept
friendly id-type aliases (`name`, `chebi`, `hmdb`, `uniprot`,
`genesymbol`, `kegg`, `pubchem`, `drugbank`, `chembl`, `cas`,
`inchi`, `inchikey`, `smiles`, `lipidmaps`, `swisslipids`, `entrez`,
`ensembl`, `iupac`, …) that the client maps to the underlying MI/OM
ontology codes. When an entity has several values for the same
id type, the **shortest** is picked as the representative.

### `lookup()`

Resolve a name (or list of names / primary keys) and pivot the
requested IDs into named columns:

```python
op.lookup(
    ['caffeine', 'metformin', 'glucose'],
    id_types=['name', 'chebi', 'hmdb', 'kegg', 'drugbank'],
)
# query     entity_pk  entity_type             name        chebi  hmdb         kegg     drugbank
# caffeine  2119890    MI:0328:Small Molecule  caffeine    27732  HMDB0001847  C07481   DB00201
# metformin 1568012    MI:0328:Small Molecule  metformin   6801   HMDB0001921  C07151   DB00331
# ...
```

Default `id_types` is `("name", "chebi", "hmdb", "uniprot",
"genesymbol")` — narrow enough to keep output readable, broad enough
for most downstream joins.

### `related()`

Pull a wide, joined relations table around a query in one call:

```python
# Compounds reported in strawberry (FooDB)
op.related(
    subject='Strawberry',
    sources=['foodb'],
    id_types=['name', 'chebi', 'hmdb'],
)

# Drug targets for caffeine (positional argument matches either side
# of the relation; subject= / object= pin a direction)
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

# Filter participants by friendly type alias
op.related(
    'metformin',
    sources=['signor'],
    participant_types=['protein'],
    id_types=['name', 'uniprot'],
)
```

Filters: `sources`, `predicates`, `relation_categories`,
`participant_types`. Layout: `subject=` / `object=` pin direction,
`group_by=` reorders rows (handy when one entity appears under several
pathway IDs), `limit=` truncates the output.

## Lower-level primitives

The wrappers are thin — when you need raw tables, paged access, or
graph export, reach for the primitives directly.

### Resolve identifiers

```python
op.resolve(['caffeine', 'TP53', 'WP253'])
# {'matches': [{'identifier': 'caffeine', 'entityPks': [2119890]}, ...],
#  'entities': [...]}
```

### Entities

```python
# All entities
df = op.entities()

# Filter by organism (NCBI taxonomy ID 9606 = human)
df = op.entities(taxonomy_ids=['9606'])

# Filter by source database
df = op.entities(sources=['hmdb'])

# Lookup by primary key
df = op.entities(entity_pks=['1568012', '8584'])
```

### Relations

```python
# All relations
df = op.relations()

# Filter by source resource
df = op.relations(sources=['signor'])

# Filter by predicate or relation category
df = op.relations(predicates=['interacts_with'])
df = op.relations(relation_categories=['membership'])

# Constrain by entity primary keys
df = op.relations(subject_entity_pks=['2401277'])  # outgoing
df = op.relations(object_entity_pks=['2233186'])   # incoming
df = op.relations(entity_pks=['2119890'])          # either side
```

### Annotations

```python
# Ontology annotations attached to entities
df = op.annotations(prefixes=['chebi'])
```

### Paged slices

```python
# Page through entities with free-text search
op.entities_slice(query='glucose', limit=20)

# Same for relations
op.relations_slice(filters={'sources': ['signor']}, limit=50)
```

## Choosing a DataFrame backend

By default, results are returned as
[polars](https://pola.rs/) DataFrames. You can choose a different
backend:

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

Relations can be returned as
[annnet](https://github.com/saezlab/annnet) graph objects:

```python
g = op.relations(as_graph=True)
```

Vertex IDs are entity primary keys; resolve them via `op.entities()`
or `op.lookup()` if you need human-readable labels.

## Ontology endpoints

Look up ontology terms, search by name, or build hierarchy trees:

```python
# Batch term lookup
result = op.ontology_terms(['GO:0006915', 'MI:0326'])

# Search terms by name (returns ranked hits across ontologies)
result = op.search_terms(['glycolysis', 'apoptosis'])

# Get a merged hierarchy tree
tree = op.ontology_tree(['GO:0006915'])

# List available ontologies
ontologies = op.ontologies()
```

## Resource catalog

```python
# What sources are available, and what each one contributes
op.resources()
# [{'resource_id': 'bindingdb', 'resource_name': 'BindingDB', 'categories': ['interaction']},
#  {'resource_id': 'foodb',     'resource_name': 'FooDB',     'categories': ['membership']},
#  ...]
```

## Cache control

Responses are cached on disk by default. Two helpers manage the cache:

```python
# Force a one-shot refresh for everything touched inside the block.
# Subsequent identical requests within the same block are served from
# the freshly populated cache.
with op.fresh():
    df = op.related('caffeine', sources=['bindingdb'])

# Wipe the entire on-disk cache (incl. the OpenAPI spec) — useful
# after a server redeploy renames endpoints or changes the schema.
op.cache_clear()
```

## Introspection

Explore available endpoints, parameters, and allowed values:

```python
# All endpoints
op.endpoints()

# Parameters for an endpoint
op.params('exports/relations/parquet')

# Allowed values for a parameter (None when free-form)
op.values('exports/entities/parquet', 'entity_types')
# ['MI:0326:Protein', 'MI:0328:Small Molecule', ...]
```

## Custom API URL

To use a different API server (e.g. a local instance):

```python
client = op.OmniPath(base_url='http://localhost:8081')
df = client.relations()
```
