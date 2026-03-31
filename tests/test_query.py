"""
Tests for query building and validation.
"""

import pytest

from omnipath_client._query import QueryBuilder
from omnipath_client._errors import (
    UnknownEndpointError,
    UnknownParameterError,
    InvalidParameterValueError,
)
from omnipath_client._inventory import Inventory


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

    def test_valid_interaction_query(self, query_builder):

        query = query_builder.build(
            'exports/interactions/parquet',
            entity_ids=['Q9Y6K9'],
            direction='directed',
        )

        assert query.params['entity_ids'] == ['Q9Y6K9']
        assert query.params['direction'] == 'directed'

    def test_unknown_endpoint(self, query_builder):

        with pytest.raises(UnknownEndpointError):
            query_builder.build('nonexistent/endpoint')

    def test_unknown_parameter(self, query_builder):

        with pytest.raises(UnknownParameterError):
            query_builder.build(
                'exports/entities/parquet',
                bogus_param='value',
            )

    def test_invalid_enum_value(self, query_builder):

        with pytest.raises(InvalidParameterValueError):
            query_builder.build(
                'exports/interactions/parquet',
                direction='sideways',
            )

    def test_valid_enum_value(self, query_builder):

        query = query_builder.build(
            'exports/interactions/parquet',
            sign='positive',
        )

        assert query.params['sign'] == 'positive'

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
