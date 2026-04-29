"""Constants and static fallback inventory for omnipath-client."""

from __future__ import annotations


DEFAULT_BASE_URL = 'https://dev.omnipathdb.org/api'
OPENAPI_PATH = '/openapi.json'

INVENTORY_CACHE_TTL = 86400  # 24 hours

# Static fallback endpoint definitions, used when the openapi.json
# cannot be fetched from the server.
STATIC_ENDPOINTS: dict[str, dict] = {
    'exports/entities/parquet': {
        'path': '/exports/entities/parquet',
        'method': 'POST',
        'summary': 'Export Entities Parquet',
        'response_format': 'parquet',
        'filters': {
            'entity_pks': {'type': 'array[integer]'},
            'entity_ids': {'type': 'array[integer]'},
            'entity_types': {'type': 'array[string]'},
            'sources': {'type': 'array[string]'},
            'taxonomy_ids': {'type': 'array[string]'},
            'ncbi_tax_id': {'type': 'array[string]'},
        },
    },
    'exports/relations/parquet': {
        'path': '/exports/relations/parquet',
        'method': 'POST',
        'summary': 'Export Relations Parquet',
        'response_format': 'parquet',
        'filters': {
            'relation_pks': {'type': 'array[integer]'},
            'subject_entity_pks': {'type': 'array[integer]'},
            'object_entity_pks': {'type': 'array[integer]'},
            'entity_pks': {'type': 'array[integer]'},
            'entity_ids': {'type': 'array[integer]'},
            'predicates': {'type': 'array[string]'},
            'interaction_types': {'type': 'array[string]'},
            'relation_categories': {'type': 'array[string]'},
            'participant_types': {'type': 'array[string]'},
            'sources': {'type': 'array[string]'},
            'annotation_terms': {'type': 'array[string]'},
            'ontology_terms': {'type': 'array[string]'},
            'annotation_scopes': {'type': 'array[string]'},
        },
    },
    'exports/annotations/parquet': {
        'path': '/exports/annotations/parquet',
        'method': 'POST',
        'summary': 'Export Annotations Parquet',
        'response_format': 'parquet',
        'filters': {
            'prefixes': {'type': 'array[string]'},
            'ontology_prefixes': {'type': 'array[string]'},
            'entity_pks': {'type': 'array[integer]'},
        },
    },
    'entities/resolve': {
        'path': '/entities/resolve',
        'method': 'POST',
        'summary': 'Resolve Entities',
        'response_format': 'json',
        'params': {
            'identifiers': {
                'type': 'array[string]',
                'required': True,
            },
        },
    },
    'entities/slice': {
        'path': '/entities/slice',
        'method': 'POST',
        'summary': 'Get Entities Slice',
        'response_format': 'json',
        'params': {
            'query': {'type': 'string'},
            'filters': {'type': 'object'},
            'limit': {'type': 'integer'},
            'offset': {'type': 'integer'},
        },
    },
    'relations/slice': {
        'path': '/relations/slice',
        'method': 'POST',
        'summary': 'Get Relations Slice',
        'response_format': 'json',
        'params': {
            'query': {'type': 'string'},
            'filters': {'type': 'object'},
            'limit': {'type': 'integer'},
            'offset': {'type': 'integer'},
        },
    },
    'resources': {
        'path': '/resources',
        'method': 'GET',
        'summary': 'Get Resources Catalog',
        'response_format': 'json',
    },
    'terms': {
        'path': '/terms',
        'method': 'POST',
        'summary': 'Get Terms Batch',
        'response_format': 'json',
        'params': {
            'term_ids': {
                'type': 'array[string]',
                'required': True,
            },
        },
    },
    'terms/search': {
        'path': '/terms/search',
        'method': 'POST',
        'summary': 'Search Terms',
        'response_format': 'json',
        'params': {
            'queries': {
                'type': 'array[string]',
                'required': True,
            },
            'limit': {
                'type': 'integer',
            },
        },
    },
    'tree': {
        'path': '/tree',
        'method': 'POST',
        'summary': 'Get Tree',
        'response_format': 'json',
        'params': {
            'term_ids': {
                'type': 'array[string]',
                'required': True,
            },
        },
    },
    'ontologies': {
        'path': '/ontologies',
        'method': 'GET',
        'summary': 'List Ontologies',
        'response_format': 'json',
    },
    'health': {
        'path': '/health',
        'method': 'GET',
        'summary': 'Health',
        'response_format': 'json',
    },
}
