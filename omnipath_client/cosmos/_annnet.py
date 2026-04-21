"""Convert COSMOS PKN DataFrames to AnnNet Graph objects.

Requires the ``annnet`` package (optional dependency).
Uses bulk operations for efficient graph construction.
"""

from __future__ import annotations

__all__ = ['to_annnet']

import logging
from typing import Any

logger = logging.getLogger(__name__)


def to_annnet(df: Any) -> Any:
    """Convert a COSMOS PKN DataFrame to an AnnNet Graph.

    Uses ``add_vertices_bulk`` and ``add_edges_bulk`` for efficient
    construction.  Entity types (protein, small_molecule) are stored
    as vertex attributes; interaction metadata as edge attributes.

    Args:
        df: COSMOS PKN DataFrame (polars or pandas) with columns:
            ``source``, ``target``, ``source_type``, ``target_type``,
            ``interaction_type``, ``resource``, ``mor``.

    Returns:
        ``annnet.Graph`` instance.

    Raises:
        ImportError: If ``annnet`` is not installed.

    Example::

        import omnipath_client as oc

        df = oc.cosmos.get_pkn('human', categories='transporters')
        g = oc.cosmos.to_annnet(df)
    """

    try:
        from annnet import Graph
    except ImportError as exc:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install with: pip install annnet'
        ) from exc

    # Normalise to dict-of-lists for column access
    # (works with both polars and pandas)
    try:
        # Polars
        cols = {c: df[c].to_list() for c in df.columns}
    except AttributeError:
        # Pandas
        cols = {c: df[c].tolist() for c in df.columns}

    n_rows = len(cols.get('source', []))

    # -- Collect unique entities with types -----------------------------------
    entity_types: dict[str, str] = {}

    for i in range(n_rows):
        src = cols['source'][i]
        tgt = cols['target'][i]
        src_type = cols.get('source_type', [None] * n_rows)[i]
        tgt_type = cols.get('target_type', [None] * n_rows)[i]

        if src not in entity_types and src_type:
            entity_types[src] = src_type
        if tgt not in entity_types and tgt_type:
            entity_types[tgt] = tgt_type

    # -- Build graph ----------------------------------------------------------
    g = Graph()

    # Bulk add vertices
    vertices = [
        {'vertex_id': vid, 'entity_type': etype}
        for vid, etype in entity_types.items()
    ]
    g.add_vertices_bulk(vertices)

    logger.info(
        'AnnNet: added %d vertices (%d protein, %d small_molecule)',
        len(vertices),
        sum(1 for v in entity_types.values() if v == 'protein'),
        sum(1 for v in entity_types.values() if v == 'small_molecule'),
    )

    # Bulk add edges
    edges = []
    mor_col = cols.get('mor', [0] * n_rows)
    itype_col = cols.get('interaction_type', [''] * n_rows)
    resource_col = cols.get('resource', [''] * n_rows)

    for i in range(n_rows):
        edges.append({
            'source': cols['source'][i],
            'target': cols['target'][i],
            'weight': float(mor_col[i]) if mor_col[i] is not None else 0.0,
            'edge_directed': True,
            'attributes': {
                'interaction_type': itype_col[i],
                'resource': resource_col[i],
            },
        })

    g.add_edges_bulk(edges)

    logger.info('AnnNet: added %d edges', len(edges))

    return g
