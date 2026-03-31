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
            'entity_ids': {'type': 'array[string]'},
            'entity_types': {'type': 'array[string]'},
            'sources': {'type': 'array[string]'},
            'taxonomy_ids': {'type': 'array[string]'},
            'ncbi_tax_id': {'type': 'array[string]'},
            'ontology_terms': {'type': 'array[string]'},
        },
    },
    'exports/interactions/parquet': {
        'path': '/exports/interactions/parquet',
        'method': 'POST',
        'summary': 'Export Interactions Parquet',
        'response_format': 'parquet',
        'filters': {
            'entity_ids': {'type': 'array[string]'},
            'member_a_id': {'type': 'string'},
            'member_b_id': {'type': 'string'},
            'interaction_types': {'type': 'array[string]'},
            'direction': {
                'type': 'enum',
                'allowed': ['any', 'directed', 'undirected'],
            },
            'sign': {
                'type': 'enum',
                'allowed': ['any', 'positive', 'negative', 'mixed'],
            },
            'has_direction': {'type': 'boolean'},
            'has_positive_sign': {'type': 'boolean'},
            'has_negative_sign': {'type': 'boolean'},
            'interaction_annotation_terms': {'type': 'array[string]'},
            'participant_annotation_terms': {'type': 'array[string]'},
            'ontology_terms': {'type': 'array[string]'},
            'sources': {'type': 'array[string]'},
        },
    },
    'exports/associations/parquet': {
        'path': '/exports/associations/parquet',
        'method': 'POST',
        'summary': 'Export Associations Parquet',
        'response_format': 'parquet',
        'filters': {
            'parent_entity_ids': {'type': 'array[string]'},
            'member_entity_ids': {'type': 'array[string]'},
            'parent_entity_types': {'type': 'array[string]'},
            'member_entity_types': {'type': 'array[string]'},
            'sources': {'type': 'array[string]'},
            'association_annotation_terms': {'type': 'array[string]'},
            'ontology_terms': {'type': 'array[string]'},
        },
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
