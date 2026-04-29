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
        assert 'exports/relations/parquet' in endpoints
        assert 'exports/annotations/parquet' in endpoints

    def test_entity_filters(self):

        endpoints = _build_static_fallback()
        ep = endpoints['exports/entities/parquet']

        assert isinstance(ep, EndpointDef)
        assert ep.method == 'POST'
        assert ep.response_format == 'parquet'
        assert 'taxonomy_ids' in ep.params
        assert 'entity_types' in ep.params

    def test_relation_filters(self):

        endpoints = _build_static_fallback()
        ep = endpoints['exports/relations/parquet']

        assert 'subject_entity_pks' in ep.params
        assert 'object_entity_pks' in ep.params
        assert 'predicates' in ep.params
        assert 'relation_categories' in ep.params


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
        assert 'exports/relations/parquet' in endpoints
        assert 'exports/annotations/parquet' in endpoints

    def test_export_endpoints_have_filters(self):

        if not OPENAPI_PATH.exists():
            return

        with open(OPENAPI_PATH) as f:
            spec = json.load(f)

        endpoints = parse_openapi(spec)
        ep = endpoints['exports/relations/parquet']

        assert ep.method == 'POST'
        assert ep.response_format == 'parquet'
        assert 'sources' in ep.params
        assert 'predicates' in ep.params

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

        params = inv.params('exports/relations/parquet')

        assert 'sources' in params
        assert isinstance(params['sources'], ParamDef)

    def test_allowed_values_unconstrained_relation_filter(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        values = inv.allowed_values(
            'exports/relations/parquet',
            'sources',
        )

        # The static fallback does not enumerate allowed sources.
        assert values is None

    def test_allowed_values_unconstrained(self):

        inv = Inventory(base_url='http://localhost:99999')
        inv.load()

        values = inv.allowed_values(
            'exports/entities/parquet',
            'taxonomy_ids',
        )

        assert values is None

    def test_loads_schema_via_downloader_without_cache_by_default(
        self,
        monkeypatch,
    ):

        calls = {}
        spec = {
            'paths': {
                '/health': {
                    'get': {
                        'summary': 'Health',
                    },
                },
            },
            'components': {
                'schemas': {},
            },
        }

        def fake_init(self, cache_dir=None, use_cache=True):
            calls['cache_dir'] = cache_dir
            calls['use_cache'] = use_cache

        def fake_fetch_json(self, url, *, params=None, force_download=False):
            calls['url'] = url
            calls['params'] = params
            calls['force_download'] = force_download
            return spec

        monkeypatch.setattr(
            'omnipath_client._download.Downloader.__init__',
            fake_init,
        )
        monkeypatch.setattr(
            'omnipath_client._download.Downloader.fetch_json',
            fake_fetch_json,
        )

        inv = Inventory(base_url='https://example.org/api')
        inv.load()

        assert calls['cache_dir'] is None
        assert calls['use_cache'] is False
        assert calls['url'] == 'https://example.org/api/openapi.json'
        assert calls['params'] is None
        assert calls['force_download'] is False
        assert 'health' in inv.endpoints

    def test_force_refresh_redownloads_schema(self, monkeypatch):

        calls: list[bool] = []
        spec = {
            'paths': {
                '/health': {
                    'get': {
                        'summary': 'Health',
                    },
                },
            },
            'components': {
                'schemas': {},
            },
        }

        def fake_init(self, cache_dir=None, use_cache=True):
            return None

        def fake_fetch_json(self, url, *, params=None, force_download=False):
            calls.append(force_download)
            return spec

        monkeypatch.setattr(
            'omnipath_client._download.Downloader.__init__',
            fake_init,
        )
        monkeypatch.setattr(
            'omnipath_client._download.Downloader.fetch_json',
            fake_fetch_json,
        )

        inv = Inventory(base_url='https://example.org/api')
        inv.load()
        inv.load(force_refresh=True)

        assert calls == [False, True]
