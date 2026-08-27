"""
Tests for query building and validation.
"""

import pytest

from omnipath_client._query import QueryBuilder
from omnipath_client._errors import (
    UnknownEndpointError,
    UnknownParameterError,
)
from omnipath_client._inventory import Inventory, parse_openapi


@pytest.fixture
def query_builder():
    """
    A QueryBuilder with static fallback inventory.
    """

    inv = Inventory(base_url='http://localhost:99999')
    inv.load()
    return QueryBuilder(inv)


class TestQueryBuilder:
    """
    Tests for QueryBuilder.build().
    """

    def test_valid_entity_query(self, query_builder):

        query = query_builder.build(
            'exports/entities/parquet',
            taxonomy_ids=['9606'],
        )

        assert query.endpoint.path == '/exports/entities/parquet'
        assert query.params == {'taxonomy_ids': ['9606']}

    def test_valid_relation_query(self, query_builder):

        query = query_builder.build(
            'exports/relations/parquet',
            entity_pks=['12345'],
            sources=['signor'],
            predicates=['interacts_with'],
        )

        assert query.endpoint.path == '/exports/relations/parquet'
        assert query.params['entity_pks'] == ['12345']
        assert query.params['sources'] == ['signor']
        assert query.params['predicates'] == ['interacts_with']

    def test_unknown_endpoint(self, query_builder):

        with pytest.raises(UnknownEndpointError):
            query_builder.build('nonexistent/endpoint')

    def test_unknown_parameter(self, query_builder):

        with pytest.raises(UnknownParameterError):
            query_builder.build(
                'exports/entities/parquet',
                bogus_param='value',
            )

    def test_none_values_skipped(self, query_builder):

        query = query_builder.build(
            'exports/entities/parquet',
            taxonomy_ids=['9606'],
            entity_types=None,
        )

        assert 'entity_types' not in query.params


class TestQueryJsonBody:
    """
    Tests for Query.json_body construction.
    """

    def test_filters_nested(self, query_builder):

        query = query_builder.build(
            'exports/entities/parquet',
            taxonomy_ids=['9606'],
            entity_types=['protein'],
        )

        body = query.json_body

        assert 'filters' in body
        assert body['filters']['taxonomy_ids'] == ['9606']
        assert body['filters']['entity_types'] == ['protein']

    def test_get_endpoint_no_body(self, query_builder):

        query = query_builder.build('health')

        assert query.json_body is None


class TestInteractionsQueries:
    """
    The interactions endpoints, whose shapes the earlier ones do not cover:
    a free-form POST body, and a dataset name that lives in the path.
    """

    @staticmethod
    def _inventory(spec):

        inv = Inventory(base_url='http://localhost:99999')
        inv._endpoints = parse_openapi(spec)
        inv._loaded = True

        return inv

    def test_unschematized_post_body_passes_through(self):
        """
        The server publishes this body as a free-form object, so the client
        has nothing to check a key against. Refusing the keys would leave the
        endpoint unreachable; the body goes through and the server answers.
        """

        inv = self._inventory({
            'paths': {
                '/interactions': {
                    'post': {'summary': 'Post Interactions'},
                },
            },
        })
        query = QueryBuilder(inv).build(
            'interactions',
            filters={'datasets': 'liana'},
            limit=5,
        )

        assert query.endpoint.method == 'POST'
        assert query.json_body == {
            'filters': {'datasets': 'liana'},
            'limit': 5,
        }

    def test_unset_parameters_are_left_out_of_the_body(self):
        """
        An option nobody set is not an option set to nothing: it must not
        reach the server, which would read it as an explicit null.
        """

        inv = self._inventory({
            'paths': {
                '/interactions': {
                    'post': {'summary': 'Post Interactions'},
                },
            },
        })
        query = QueryBuilder(inv).build(
            'interactions',
            filters={},
            collapse=None,
            cursor=None,
        )

        assert query.json_body == {'filters': {}}

    def test_dataset_name_reaches_the_path_and_not_the_query(self):
        """
        A path parameter is already spent on the URL. Repeating it in the
        query string states the same thing twice, and the two can disagree.
        """

        inv = self._inventory({
            'paths': {
                '/interactions/{dataset}': {
                    'get': {
                        'summary': 'Get Interactions Dataset',
                        'parameters': [
                            {
                                'name': 'dataset',
                                'in': 'path',
                                'required': True,
                                'schema': {'type': 'string'},
                            },
                            {
                                'name': 'limit',
                                'in': 'query',
                                'schema': {'type': 'integer'},
                            },
                        ],
                    },
                },
            },
        })
        query = QueryBuilder(inv).build(
            'interactions/{dataset}',
            dataset='metalinksdb',
            limit=10,
        )

        assert query.resolved_url.endswith('/interactions/metalinksdb')
        assert query.query_params == {'limit': 10}
