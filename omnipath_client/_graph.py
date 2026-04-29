"""Conversion of relations DataFrames to annnet Graphs."""

from __future__ import annotations

from typing import Any

from omnipath_client._session import get_logger


logger = get_logger(__name__)


def relations_to_graph(df: Any) -> Any:
    """Convert a relations DataFrame to an annnet Graph.

    Maps relation columns to annnet edge format:
    ``subject_entity_pk`` -> source, ``object_entity_pk`` -> target.
    Vertex IDs are entity primary keys; resolve them via
    ``OmniPath.entities_slice`` if you need human-readable labels.

    Args:
        df:
            A relations DataFrame (any backend).

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

    logger.info('Converting relations DataFrame to annnet graph')

    # Convert to polars if needed (annnet is polars-backed)
    if not isinstance(df, pl.DataFrame):
        import narwhals as nw

        nw_df = nw.from_native(df, eager_only=True)
        df = nw_df.to_native()
        logger.debug('Converted relations frame to polars backend')

    g = annnet.Graph(directed=True)

    all_pks = pl.concat(
        [
            df.select(pl.col('subject_entity_pk').alias('pk')),
            df.select(pl.col('object_entity_pk').alias('pk')),
        ]
    ).unique()

    g.add_vertices(all_pks['pk'].to_list())

    for row in df.iter_rows(named=True):
        g.add_edge(
            row['subject_entity_pk'],
            row['object_entity_pk'],
        )

    logger.info('Created relations graph with %d edges', df.height)
    return g
