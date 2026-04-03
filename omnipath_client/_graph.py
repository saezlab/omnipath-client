"""Conversion of interaction and association DataFrames to annnet Graphs."""

from __future__ import annotations

import io
import logging
import os
import time
from typing import Any

import narwhals as nw
import numpy as np

try:
    import polars as pl
except Exception:
    pl = None


logger = logging.getLogger(__name__)

_ANN_URL = "https://archive.omnipathdb.org/omnipath_webservice_annotations__latest.tsv.gz"
_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".cache", "annnet", "omnipath_annotations.tsv.gz")

_SOURCE_CANDIDATES = [
    "source",
    "source_genesymbol",
    "source_gene_symbol",
    "source_gene",
    "source_uniprot",
    "source_id",
]
_TARGET_CANDIDATES = [
    "target",
    "target_genesymbol",
    "target_gene_symbol",
    "target_gene",
    "target_uniprot",
    "target_id",
]
_DIRECTED_CANDIDATES = ["is_directed", "directed", "consensus_direction"]
_WEIGHT_CANDIDATES = ["weight", "consensus_weight", "score"]
_EDGE_ID_CANDIDATES = ["edge_id", "interaction_id", "id"]
_SLICE_CANDIDATES = ["slice", "slice_id"]

_DATASET_MAP = None  # populated lazily to avoid importing omnipath at module load


def _dataset_map():
    global _DATASET_MAP
    if _DATASET_MAP is not None:
        return _DATASET_MAP
    try:
        from omnipath import interactions as opi
    except Exception as exc:
        raise ImportError(
            "omnipath package is required to fetch from the OmniPath web service. "
            "Install with `pip install omnipath` or pass a dataframe as `df=`."
        ) from exc
    _DATASET_MAP = {
        "omnipath": opi.OmniPath,
        "all": opi.AllInteractions,
        "posttranslational": opi.PostTranslational,
        "pathwayextra": opi.PathwayExtra,
        "kinaseextra": opi.KinaseExtra,
        "ligrecextra": opi.LigRecExtra,
        "dorothea": opi.Dorothea,
        "tftarget": opi.TFtarget,
        "transcriptional": opi.Transcriptional,
        "tfmirna": opi.TFmiRNA,
        "mirna": opi.miRNA,
        "lncrnamrna": opi.lncRNAmRNA,
        "collectri": opi.CollecTRI,
    }
    return _DATASET_MAP


def _pick_col(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None


def _is_null(x):
    if x is None:
        return True
    try:
        if isinstance(x, (float, np.floating)):
            return bool(np.isnan(x))
    except Exception:
        pass
    return False


def _coerce_bool(x, default):
    if x is None:
        return default
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, np.integer)):
        return bool(x)
    if isinstance(x, str):
        v = x.strip().lower()
        if v in {"1", "true", "t", "yes", "y", "directed", "dir"}:
            return True
        if v in {"0", "false", "f", "no", "n", "undirected", "undir", "u"}:
            return False
    return default


def _to_dicts(native, ndf):
    if pl is not None and isinstance(native, pl.DataFrame):
        return native.to_dicts()
    if hasattr(native, "to_dict"):
        try:
            return native.to_dict(orient="records")
        except Exception:
            pass
    if hasattr(ndf, "to_dicts"):
        return ndf.to_dicts()
    raise TypeError("Unsupported dataframe type for OmniPath import")


def _fetch_df(dataset, include, exclude, query):
    def _norm(s):
        return s.lower().replace("-", "").replace("_", "")

    dataset_key = _norm(dataset)
    classes = _dataset_map()

    if dataset_key not in classes:
        raise ValueError(f"Unknown dataset {dataset!r}. Try one of: {sorted(classes.keys())}")

    query = query or {}
    cls = classes[dataset_key]
    if dataset_key == "all":
        return cls.get(include=include, exclude=exclude, **query)
    elif dataset_key == "posttranslational":
        return cls.get(exclude=exclude, **query)
    else:
        return cls.get(**query)


def _load_annotation_archive(
    vertex_annotations_df,
    vertex_annotations_path,
):
    if vertex_annotations_df is not None:
        try:
            ann_raw = nw.from_native(vertex_annotations_df, eager_only=True)
            return nw.to_native(ann_raw)
        except Exception as e:
            logger.warning("vertex_annotations_df could not be read: %s", e)
            return None

    if vertex_annotations_path is not None:
        try:
            return pl.read_csv(vertex_annotations_path, separator="\t")
        except Exception as e:
            logger.warning("vertex_annotations_path failed: %s", e)
            return None

    try:
        import requests as _requests

        if os.path.exists(_CACHE_PATH):
            logger.debug("vertex annotations: loading from cache %s", _CACHE_PATH)
            t = time.perf_counter()
            ann = pl.read_csv(_CACHE_PATH, separator="\t")
            logger.debug("vertex annotations: loaded in %.1fs  shape=%s", time.perf_counter() - t, ann.shape)
            return ann

        logger.info("vertex annotations: downloading from OmniPath archive (~114 MB, one-time)...")
        t = time.perf_counter()
        resp = _requests.get(_ANN_URL, stream=True, timeout=(5, 60))
        resp.raise_for_status()
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "wb") as f:
            f.write(resp.content)
        ann = pl.read_csv(io.BytesIO(resp.content), separator="\t")
        logger.info(
            "vertex annotations: downloaded + cached in %.1fs → %s",
            time.perf_counter() - t,
            _CACHE_PATH,
        )
        return ann
    except Exception as e:
        logger.warning("vertex annotations download failed: %s", e)
        return None


def _attach_vertex_annotations(G, all_vids, ann_raw, vertex_annotation_sources):
    if ann_raw is None:
        return

    try:
        if not isinstance(ann_raw, pl.DataFrame):
            ann_raw = pl.from_pandas(ann_raw)

        vids_set = set(all_vids)
        mask = pl.col("genesymbol").is_in(vids_set)
        if vertex_annotation_sources is not None:
            mask = mask & pl.col("source").is_in(vertex_annotation_sources)
        ann = ann_raw.filter(mask)

        flat = (
            ann.with_columns(
                pl.concat_str([pl.col("source"), pl.col("label")], separator=":").alias("attr_key")
            )
            .group_by(["genesymbol", "attr_key"])
            .agg(pl.col("value").cast(pl.Utf8).drop_nulls().unique().sort().str.join(";"))
            .pivot(on="attr_key", index="genesymbol", values="value")
            .rename({"genesymbol": "vertex_id"})
        )

        G.add_vertices_bulk(
            [
                (
                    row["vertex_id"],
                    {k: v for k, v in row.items() if k != "vertex_id" and v is not None},
                )
                for row in flat.to_dicts()
                if row["vertex_id"] in G.entity_to_idx
            ]
        )
        logger.debug("vertex annotations: loaded shape=%s", G.vertex_attributes.shape)
    except Exception as e:
        logger.warning("vertex annotation pivot/load failed: %s", e)


def read_omnipath(
    df=None,
    *,
    dataset: str = "omnipath",
    include=None,
    exclude=None,
    query: dict | None = None,
    source_col: str | None = None,
    target_col: str | None = None,
    directed_col: str | None = None,
    weight_col: str | None = None,
    edge_id_col: str | None = None,
    slice_col: str | None = None,
    slice: str | None = None,
    default_directed: bool = True,
    edge_attr_cols: list[str] | None = None,
    dropna: bool = True,
    annotations_backend: str = "polars",
    vertex_annotations_df=None,
    vertex_annotations_path: str | None = None,
    vertex_annotation_sources: list[str] | None = None,
    load_vertex_annotations: bool = True,
    **graph_kwargs,
):
    """Build an AnnNet from OmniPath interaction data, with edge and vertex annotations.

    Fetches a signaling interaction dataset from the OmniPath web service (or accepts
    a pre-loaded DataFrame), builds the graph structure via bulk operations, and
    optionally enriches vertices with annotations from the OmniPath annotation archive.

    The annotation archive (~114MB) is downloaded once and cached at
    ``~/.cache/annnet/omnipath_annotations.tsv.gz`` for fast subsequent loads.

    Parameters
    ----------
    df : DataFrame-like, optional
        If provided, skip the OmniPath network request and build from this table.
        Must contain at least source and target columns. Accepts Polars, pandas,
        or any Narwhals-compatible DataFrame.
    dataset : str, optional
        OmniPath interaction dataset to fetch. One of:
        ``"omnipath"`` (default, curated core), ``"all"``, ``"posttranslational"``,
        ``"pathwayextra"``, ``"kinaseextra"``, ``"ligrecextra"``, ``"dorothea"``,
        ``"tftarget"``, ``"transcriptional"``, ``"tfmirna"``, ``"mirna"``,
        ``"lncrnamrna"``, ``"collectri"``.
    include, exclude : optional
        Dataset include/exclude filters. Only used when ``dataset="all"``
        (include/exclude) or ``dataset="posttranslational"`` (exclude only).
    query : dict, optional
        Extra query parameters forwarded to the OmniPath web service.
        Example: ``{"organism": "human", "genesymbols": True}``.
    source_col : str, optional
        Column name for source node identifiers. Auto-detected from common
        OmniPath field names if omitted.
    target_col : str, optional
        Column name for target node identifiers. Auto-detected if omitted.
    directed_col : str, optional
        Column holding per-edge directedness flags (bool-like).
    weight_col : str, optional
        Column holding edge weights. Defaults to 1.0 if omitted.
    edge_id_col : str, optional
        Column holding stable edge identifiers.
    slice_col : str, optional
        Column holding per-edge slice identifiers.
    slice : str, optional
        Slice to place all edges into. Ignored if ``slice_col`` is provided.
    default_directed : bool, optional
        Fallback directedness when ``directed_col`` is missing or null. Default ``True``.
    edge_attr_cols : list[str], optional
        Columns to store as edge attributes. Defaults to all non-structural columns.
        Pass ``[]`` to skip edge attributes entirely.
    dropna : bool, optional
        Drop rows with null source or target (default ``True``). If ``False``, raise on first null.
    annotations_backend : str, optional
        Backend for AnnNet attribute tables. Default ``"polars"``.
    vertex_annotations_df : DataFrame-like, optional
        Pre-loaded annotation table in OmniPath long format ``(genesymbol, source, label, value)``.
    vertex_annotations_path : str, optional
        Path to a local OmniPath annotation file (``.tsv`` or ``.tsv.gz``).
    vertex_annotation_sources : list[str], optional
        OmniPath annotation resource names to include as vertex attributes.
        If omitted, all resources are loaded.
    load_vertex_annotations : bool, optional
        Set to ``False`` to skip annotation loading entirely. Default ``True``.
    **graph_kwargs
        Forwarded to the ``AnnNet`` constructor.

    Returns
    -------
    AnnNet
        Fully constructed graph.

    Examples
    --------
    Structure only, no annotations::

        G = read_omnipath(load_vertex_annotations=False)

    Full load::

        G = read_omnipath(
            dataset="omnipath",
            query={"organism": "human", "genesymbols": True},
            source_col="source_genesymbol",
            target_col="target_genesymbol",
            edge_attr_cols=["is_stimulation", "is_inhibition", "n_sources", "n_references"],
            vertex_annotation_sources=["HGNC", "CancerGeneCensus", "UniProt_location"],
        )

    From a custom DataFrame::

        G = read_omnipath(df=my_df, load_vertex_annotations=False)
    """
    try:
        import annnet as an
    except ImportError as e:
        raise ImportError(
            "annnet is required for graph conversion. "
            "Install it with: pip install annnet"
        ) from e

    if df is None:
        df = _fetch_df(dataset, include, exclude, query)

    ndf = nw.from_native(df, eager_only=True)
    native = nw.to_native(ndf)
    cols = list(getattr(native, "columns", ndf.columns))

    if source_col is None:
        source_col = _pick_col(cols, _SOURCE_CANDIDATES)
    if target_col is None:
        target_col = _pick_col(cols, _TARGET_CANDIDATES)

    if source_col is None or target_col is None:
        raise ValueError(
            "Could not infer source/target columns. Pass source_col and target_col explicitly."
        )

    if directed_col is None:
        directed_col = _pick_col(cols, _DIRECTED_CANDIDATES)
    if weight_col is None:
        weight_col = _pick_col(cols, _WEIGHT_CANDIDATES)
    if edge_id_col is None:
        edge_id_col = _pick_col(cols, _EDGE_ID_CANDIDATES)
    if slice_col is None:
        slice_col = _pick_col(cols, _SLICE_CANDIDATES)

    if edge_attr_cols is None:
        structural = {source_col, target_col, directed_col, weight_col, edge_id_col, slice_col}
        edge_attr_cols = [c for c in cols if c not in structural]

    G = an.AnnNet(
        directed=default_directed,
        annotations_backend=annotations_backend,
        n=len(ndf),
        e=len(ndf),
        **graph_kwargs,
    )
    G._history_enabled = False

    rows = _to_dicts(native, ndf)
    bulk = []
    for row in rows:
        s = row.get(source_col)
        t = row.get(target_col)
        if dropna and (_is_null(s) or _is_null(t)):
            continue
        if _is_null(s) or _is_null(t):
            raise ValueError("Found null source/target with dropna=False.")

        edge_dir = (
            _coerce_bool(row.get(directed_col), default_directed)
            if directed_col
            else default_directed
        )
        w_raw = row.get(weight_col) if weight_col else None
        w = 1.0 if _is_null(w_raw) else float(w_raw)
        eid = None
        if edge_id_col:
            eid_raw = row.get(edge_id_col)
            if not _is_null(eid_raw):
                eid = str(eid_raw)
        edge_slice = slice
        if slice_col:
            s_raw = row.get(slice_col)
            if not _is_null(s_raw):
                edge_slice = str(s_raw)

        bulk.append(
            {
                "source": str(s),
                "target": str(t),
                "weight": w,
                "edge_id": eid,
                "edge_directed": edge_dir,
                "slice": edge_slice,
                "attributes": {c: row.get(c) for c in edge_attr_cols if c in row},
            }
        )

    G.add_edges_bulk(bulk)
    G._history_enabled = True

    all_vids = [vid for vid, t in G.entity_types.items() if t == "vertex"]
    G.add_vertices_bulk(all_vids)

    if load_vertex_annotations:
        ann_raw = _load_annotation_archive(vertex_annotations_df, vertex_annotations_path)
        _attach_vertex_annotations(G, all_vids, ann_raw, vertex_annotation_sources)

    return G


def interactions_to_annnet(df: Any = None, **kwargs: Any) -> Any:
    """Convert an interactions DataFrame to an annnet Graph.

    Args:
        df:
            An interactions DataFrame (any backend).

    Returns:
        An ``annnet.AnnNet`` instance.
    """
    return read_omnipath(df=df, **kwargs)


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

    Associations represent parent-member relationships (complexes, pathways, reactions).

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
            "annnet is required for graph conversion. "
            "Install it with: pip install annnet"
        ) from e

    ndf = nw.from_native(df, eager_only=True)
    native = nw.to_native(ndf)
    rows = _to_dicts(native, ndf)
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
        bucket = grouped.setdefault(key, {"members": [], "attrs": {}})
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


__all__ = ["associations_to_annnet", "interactions_to_annnet", "read_omnipath"]