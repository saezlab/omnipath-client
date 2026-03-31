"""Conversion of interaction and association DataFrames to annnet Graphs."""

from __future__ import annotations

from typing import Any
import logging

import narwhals as nw


logger = logging.getLogger(__name__)


def interactions_to_annnet(df: Any = None, **kwargs: Any) -> Any:
    """Convert an interactions DataFrame to an annnet Graph.

    Maps interaction columns to the annnet OmniPath loader and returns an
    ``annnet.AnnNet`` instance.

    Args:
        df:
            An interactions DataFrame (any backend).

    Returns:
        An ``annnet.AnnNet`` instance.
    """

    try:
        import annnet as an
    except ImportError as e:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install it with: pip install annnet',
        ) from e

    return an.read_omnipath(df=df, **kwargs)


def associations_to_annnet(
    df: Any,
    *,
    parent_col: str = "parent_entity_id",
    member_col: str = "member_entity_id",
    edge_id_col: str | None = None,
    edge_attr_cols: list[str] | None = None,
    min_members: int = 2,
    **graph_kwargs: Any,
) -> Any:
    """Convert an associations DataFrame to an annnet Graph.

    Associations represent parent-member relationships (complexes,
    pathways, reactions).

    Args:
        df:
            An associations DataFrame (any backend).

    Returns:
        An ``annnet.AnnNet`` instance.
    """

    try:
        import annnet as an
    except ImportError as e:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install it with: pip install annnet',
        ) from e

    ndf = nw.from_native(df, eager_only=True)
    rows = ndf.to_dicts()
    if not rows:
        return an.AnnNet(**graph_kwargs)

    sample = rows[0]
    missing = [col for col in (parent_col, member_col) if col not in sample]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    graph = an.AnnNet(**graph_kwargs)
    grouped: dict[str, dict[str, Any]] = {}
    all_vertices: set[str] = set()

    for row in rows:
        parent = row.get(parent_col)
        member = row.get(member_col)
        if parent is None or member is None:
            continue

        edge_id = row.get(edge_id_col) if edge_id_col else parent
        key = str(edge_id)
        member_id = str(member)
        parent_id = str(parent)
        bucket = grouped.setdefault(
            key,
            {
                "members": [],
                "attrs": {},
            },
        )
        bucket["members"].append(member_id)
        all_vertices.add(member_id)
        all_vertices.add(parent_id)

        if edge_attr_cols is None:
            attrs = {
                k: v
                for k, v in row.items()
                if k not in {parent_col, member_col}
                and (edge_id_col is None or k != edge_id_col)
                and v is not None
            }
        else:
            attrs = {k: row.get(k) for k in edge_attr_cols if row.get(k) is not None}

        bucket["attrs"].update(attrs)
        bucket["attrs"].setdefault("parent_entity_id", parent)

    hyperedges = []
    for edge_id, payload in grouped.items():
        members = list(dict.fromkeys(payload["members"]))
        if len(members) < min_members:
            continue

        hyperedges.append(
            {
                "members": members,
                "edge_id": edge_id,
                "edge_directed": False,
                "attrs": payload["attrs"],
            }
        )

    if all_vertices:
        graph.add_vertices_bulk(sorted(all_vertices))
    if hyperedges:
        graph.add_hyperedges_bulk(hyperedges)

    return graph


def read_omnipath(*args: Any, **kwargs: Any) -> Any:
    """Load OmniPath data into an annnet Graph.

    This is a thin wrapper around ``annnet.read_omnipath``.

    Args:
        *args:
            Positional arguments forwarded to ``annnet.read_omnipath``.
        **kwargs:
            Keyword arguments forwarded to ``annnet.read_omnipath``.

    Returns:
        An ``annnet.AnnNet`` instance.
    """

    try:
        import annnet as an
    except ImportError as e:
        raise ImportError(
            'annnet is required for graph conversion. '
            'Install it with: pip install annnet',
        ) from e

    return an.read_omnipath(*args, **kwargs)


__all__ = ["associations_to_annnet", "interactions_to_annnet", "read_omnipath"]
