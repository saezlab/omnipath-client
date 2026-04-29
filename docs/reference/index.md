# API Reference

## Client

::: omnipath_client.OmniPath
    options:
        show_source: false
        members_order: source

## Module-level functions

### High-level helpers

::: omnipath_client.lookup
    options:
        show_source: false

::: omnipath_client.related
    options:
        show_source: false

### Export endpoints

::: omnipath_client.entities
    options:
        show_source: false

::: omnipath_client.relations
    options:
        show_source: false

::: omnipath_client.annotations
    options:
        show_source: false

### Lookup and slice

::: omnipath_client.resolve
    options:
        show_source: false

::: omnipath_client.entities_slice
    options:
        show_source: false

::: omnipath_client.relations_slice
    options:
        show_source: false

::: omnipath_client.resources
    options:
        show_source: false

### Ontology

::: omnipath_client.ontology_terms
    options:
        show_source: false

::: omnipath_client.ontology_tree
    options:
        show_source: false

::: omnipath_client.search_terms
    options:
        show_source: false

::: omnipath_client.ontologies
    options:
        show_source: false

### Cache control

::: omnipath_client.cache_clear
    options:
        show_source: false

::: omnipath_client.fresh
    options:
        show_source: false

## Response parsing

::: omnipath_client._response.parse_response
    options:
        show_source: false

## Graph conversion

::: omnipath_client._graph.relations_to_graph
    options:
        show_source: false

## Pivots and aliases

::: omnipath_client._pivot.ID_ALIASES
    options:
        show_source: false

::: omnipath_client._pivot.PARTICIPANT_TYPE_ALIASES
    options:
        show_source: false

::: omnipath_client._pivot.pivot_identifiers
    options:
        show_source: false

::: omnipath_client._pivot.join_relations_with_entities
    options:
        show_source: false

## Inventory

::: omnipath_client._inventory.Inventory
    options:
        show_source: false
        members_order: source

## Query

::: omnipath_client._query.QueryBuilder
    options:
        show_source: false

::: omnipath_client._query.Query
    options:
        show_source: false
        members_order: source

## Data classes

::: omnipath_client._endpoints.EndpointDef
    options:
        show_source: false

::: omnipath_client._endpoints.ParamDef
    options:
        show_source: false

## Exceptions

::: omnipath_client._errors
    options:
        show_source: false
        members_order: source

---

## Utils: ID Translation

::: omnipath_client.utils.map_name
    options:
        show_source: false

::: omnipath_client.utils.map_names
    options:
        show_source: false

::: omnipath_client.utils.map_name0
    options:
        show_source: false

::: omnipath_client.utils.translate
    options:
        show_source: false

::: omnipath_client.utils.translate_column
    options:
        show_source: false

::: omnipath_client.utils.translate_columns
    options:
        show_source: false

::: omnipath_client.utils.id_types
    options:
        show_source: false

## Utils: Taxonomy

::: omnipath_client.utils.resolve_organism
    options:
        show_source: false

::: omnipath_client.utils.ensure_ncbi_tax_id
    options:
        show_source: false

::: omnipath_client.utils.ensure_common_name
    options:
        show_source: false

::: omnipath_client.utils.ensure_latin_name
    options:
        show_source: false

::: omnipath_client.utils.all_organisms
    options:
        show_source: false

## Utils: Orthology

::: omnipath_client.utils.orthology_translate
    options:
        show_source: false

::: omnipath_client.utils.orthology_translate_column
    options:
        show_source: false

## Utils: Reference Lists

::: omnipath_client.utils.get_reflist
    options:
        show_source: false

::: omnipath_client.utils.all_swissprots
    options:
        show_source: false

::: omnipath_client.utils._reflists.all_trembls
    options:
        show_source: false

::: omnipath_client.utils.is_swissprot
    options:
        show_source: false

## Utils: Configuration

::: omnipath_client.utils._base.set_utils_url
    options:
        show_source: false

::: omnipath_client.utils._base.get_utils_url
    options:
        show_source: false
