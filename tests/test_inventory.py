"""
Tests for API inventory loading and parsing.
"""

import json
from pathlib import Path

from omnipath_client._endpoints import ParamDef, EndpointDef
from omnipath_client._inventory import (
    Inventory,
    parse_openapi,
    _build_static_fallback,
)


OPENAPI_PATH = Path(__file__).parent.parent / 'planning' / 'openapi.json'


class TestStaticFallback:
    """
    Tests for the static fallback inventory.
    """

    def test_builds_endpoints(self):

        endpoints = _build_static_fallback()

        assert len(endpoints) > 0
        assert 'exports/entities/parquet' in endpoints
        assert 'exports/interactions/parquet' in endpoints
        assert 'exports/associations/parquet' in endpoints

    def test_entity_filters(self):

        endpoints = _build_static_fallback()
        ep = endpoints['exports/entities/parquet']

        assert isinstance(ep, EndpointDef)
        assert ep.method == 'POST'
        assert ep.response_format == 'parquet'
        assert 'taxonomy_ids' in ep.params
        assert 'entity_types' in ep.params

    def test_interaction_filters(self):

        endpoints = _build_static_fallback()
        ep = endpoints['exports/interactions/parquet']

        assert 'direction' in ep.params
        pdef = ep.params['direction']
        assert pdef.allowed_values == [
            'any',
            'directed',
            'undirected',
        ]


class TestParseOpenapi:
    """
    Tests for OpenAPI spec parsing.
    """

    def test_parse_local_spec(self):

        if not OPENAPI_PATH.exists():
            return

        with open(OPENAPI_PATH) as f:
            spec = json.load(f)

        endpoints = parse_openapi(spec)

        assert len(endpoints) > 0
        assert 'exports/entities/parquet' in endpoints
        assert 'exports/interactions/parquet' in endpoints
        assert 'exports/associations/parquet' in endpoints

    def test_export_endpoints_have_filters(self):

        if not OPENAPI_PATH.exists():
            return

        with open(OPENAPI_PATH) as f:
            spec = json.load(f)

        endpoints = parse_openapi(spec)
        ep = endpoints['exports/interactions/parquet']

        assert ep.method == 'POST'
        assert ep.response_format == 'parquet'
        assert 'entity_ids' in ep.params
        assert 'direction' in ep.params

        direction = ep.params['direction']
        assert direction.allowed_values == [
            'any',
            'directed',
            'undirected',
        ]

    def test_ontology_endpoints(self):

        if not OPENAPI_PATH.exists():
            return

        with open(OPENAPI_PATH) as f:
            spec = json.load(f)

        endpoints = parse_openapi(spec)

        assert 'terms' in endpoints
        assert 'tree' in endpoints
        assert 'ontologies' in endpoints


class TestInventory:
    """
    Tests for the Inventory class.
    """

    def test_fallback_on_bad_url(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        assert len(inv.endpoints) > 0
        assert 'exports/entities/parquet' in inv.endpoints

    def test_params_method(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        params = inv.params('exports/interactions/parquet')

        assert 'entity_ids' in params
        assert isinstance(params['entity_ids'], ParamDef)

    def test_allowed_values_method(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        values = inv.allowed_values(
            'exports/interactions/parquet',
            'direction',
        )

        assert values == ['any', 'directed', 'undirected']

    def test_allowed_values_unconstrained(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        values = inv.allowed_values(
            'exports/entities/parquet',
            'taxonomy_ids',
        )

        assert values is None
