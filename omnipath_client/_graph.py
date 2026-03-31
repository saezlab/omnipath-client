"""Conversion of interaction and association DataFrames to annnet Graphs."""

from __future__ import annotations

from typing import Any
import logging


logger = logging.getLogger(__name__)


def interactions_to_graph(df: Any) -> Any:
    """Convert an interactions DataFrame to an annnet Graph.

    Maps interaction columns to annnet edge format:
    ``member_a_id`` -> source, ``member_b_id`` -> target.

    Args:
        df:
            An interactions DataFrame (any backend).

    Returns:
        An ``annnet.Graph`` instance.
    """

    try:
        import annnet
    except ImportError as e:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install it with: pip install annnet',
        ) from e

    import polars as pl

    # Convert to polars if needed (annnet is polars-backed)
    if not isinstance(df, pl.DataFrame):
        import narwhals as nw

        nw_df = nw.from_native(df, eager_only=True)
        df = nw_df.to_native()

    g = annnet.Graph(directed=True)

    # Add vertices from both member columns
    all_ids = pl.concat(
        [
            df.select(pl.col('member_a_id').alias('id')),
            df.select(pl.col('member_b_id').alias('id')),
        ]
    ).unique()

    g.add_vertices(all_ids['id'].to_list())

    # Add edges
    for row in df.iter_rows(named=True):
        g.add_edge(
            row['member_a_id'],
            row['member_b_id'],
            directed=row.get('is_directed', True),
        )

    return g


def associations_to_graph(df: Any) -> Any:
    """Convert an associations DataFrame to an annnet Graph.

    Associations represent parent-member relationships (complexes,
    pathways, reactions).

    Args:
        df:
            An associations DataFrame (any backend).

    Returns:
        An ``annnet.Graph`` instance.
    """

    try:
        import annnet
    except ImportError as e:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install it with: pip install annnet',
        ) from e

    import polars as pl

    if not isinstance(df, pl.DataFrame):
        import narwhals as nw

        nw_df = nw.from_native(df, eager_only=True)
        df = nw_df.to_native()

    g = annnet.Graph(directed=True)

    # Collect all unique entity IDs
    all_ids = pl.concat(
        [
            df.select(pl.col('parent_entity_id').alias('id')),
            df.select(pl.col('member_entity_id').alias('id')),
        ]
    ).unique()

    g.add_vertices(all_ids['id'].to_list())

    # Add edges from parent to member
    for row in df.iter_rows(named=True):
        g.add_edge(
            row['parent_entity_id'],
            row['member_entity_id'],
        )

    return g
