"""
Tests for response parsing and backend conversion.
"""

import pytest

from omnipath_client._response import parse_response


class TestParseResponseParquet:
    """
    Tests for Parquet response parsing.
    """

    def test_polars_backend(self, entities_parquet):

        import polars as pl

        df = parse_response(entities_parquet, 'parquet', 'polars')

        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] > 0
        assert 'entity_id' in df.columns

    def test_pandas_backend(self, entities_parquet):

        import pandas as pd

        df = parse_response(entities_parquet, 'parquet', 'pandas')

        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] > 0
        assert 'entity_id' in df.columns

    def test_pyarrow_backend(self, entities_parquet):

        import pyarrow as pa

        table = parse_response(entities_parquet, 'parquet', 'pyarrow')

        assert isinstance(table, pa.Table)
        assert table.num_rows > 0
        assert 'entity_id' in table.column_names

    def test_interactions_parquet(self, interactions_parquet):

        import polars as pl

        df = parse_response(
            interactions_parquet,
            'parquet',
            'polars',
        )

        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] > 0
        assert 'member_a_id' in df.columns
        assert 'member_b_id' in df.columns
        assert 'interaction_type' in df.columns

    def test_associations_parquet(self, associations_parquet):

        import polars as pl

        df = parse_response(
            associations_parquet,
            'parquet',
            'polars',
        )

        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] > 0
        assert 'parent_entity_id' in df.columns
        assert 'member_entity_id' in df.columns

    def test_auto_backend(self, entities_parquet):

        df = parse_response(entities_parquet, 'parquet', 'auto')

        assert df is not None
        assert hasattr(df, 'shape') or hasattr(df, 'num_rows')

    def test_unsupported_format(self, entities_parquet):

        with pytest.raises(ValueError, match='Unsupported'):
            parse_response(entities_parquet, 'csv', 'polars')
