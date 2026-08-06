"""Turn an OmniPath table into an AnnNet graph.

An interaction table is a graph written as rows: two of its columns name the
endpoints of an edge, and the rest describe that edge. :func:`to_annnet` reads
the table, works out which column is which, and builds the graph in one bulk
write.

The direction of the dependency is the point. This package knows about AnnNet,
and AnnNet knows nothing about OmniPath: a general network data structure that
downloads one knowledge base is not general, and every user of it pays for a
dependency they do not use.
"""

from __future__ import annotations


__all__ = ['to_annnet', 'annotate_nodes', 'node_annotations']

import math
from typing import TYPE_CHECKING, Any

from omnipath_client._session import get_logger


if TYPE_CHECKING:  # pragma: no cover - for the type checker alone
    from annnet import AnnNet


logger = get_logger(__name__)

# The archive of node annotations. It is one large file, so it is downloaded
# once and read from the cache after that, through the same download manager
# every other request of this package goes through.
ANNOTATIONS_URL = 'https://archive.omnipathdb.org/omnipath_webservice_annotations__latest.tsv.gz'

# Which column names an endpoint, in the order they are tried. The first list
# covers the relations export of the web service and the second the interaction
# tables that name their endpoints by gene or by protein.
SOURCE_COLUMNS = (
    'subject_entity_pk',
    'source',
    'source_genesymbol',
    'source_gene_symbol',
    'source_gene',
    'source_uniprot',
    'source_id',
)
TARGET_COLUMNS = (
    'object_entity_pk',
    'target',
    'target_genesymbol',
    'target_gene_symbol',
    'target_gene',
    'target_uniprot',
    'target_id',
)
DIRECTED_COLUMNS = ('is_directed', 'directed', 'consensus_direction')
WEIGHT_COLUMNS = ('weight', 'consensus_weight', 'score')
EDGE_ID_COLUMNS = ('edge_id', 'interaction_id', 'relation_pk', 'id')
SLICE_COLUMNS = ('slice', 'slice_id')

_TRUE_WORDS = frozenset({'1', 'true', 't', 'yes', 'y', 'directed', 'dir'})
_FALSE_WORDS = frozenset(
    {'0', 'false', 'f', 'no', 'n', 'undirected', 'undir', 'u'}
)


def _require_annnet() -> Any:
    try:
        import annnet
    except ImportError as error:
        raise ImportError(
            'annnet is required to build a graph. Install it with: '
            'pip install "omnipath-client[annnet]"',
        ) from error
    return annnet


def _rows(df: Any) -> tuple[list[str], Any]:
    """Return the column names of a table and an iterator over its rows.

    The rows are streamed rather than materialized. An interaction table runs
    to millions of rows, and holding the whole of it as dictionaries beside the
    graph being built costs twice what building the graph does.
    """
    import narwhals as nw

    frame = nw.from_native(df, eager_only=True, pass_through=False)
    return list(frame.columns), frame.iter_rows(named=True)


def _pick(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        if name in columns:
            return name
    return None


def _is_null(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _as_edge_id(value: Any) -> str | None:
    if _is_null(value):
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        word = value.strip().lower()
        if word in _TRUE_WORDS:
            return True
        if word in _FALSE_WORDS:
            return False
    return default


def to_annnet(
    df: Any,
    *,
    source_col: str | None = None,
    target_col: str | None = None,
    directed_col: str | None = None,
    weight_col: str | None = None,
    edge_id_col: str | None = None,
    slice_col: str | None = None,
    slice: str | None = None,
    directed: bool = True,
    edge_attr_cols: list[str] | None = None,
    dropna: bool = True,
    **graph_kwargs: Any,
) -> AnnNet:
    """Build an AnnNet graph from an OmniPath table.

    One row is one edge. Two columns name its endpoints, and every other column
    becomes an attribute of that edge unless ``edge_attr_cols`` says otherwise.

    Args:
        df:
            Any table narwhals reads: polars, pandas or pyarrow. The relations
            export and the interaction tables are both read without options,
            because the column names of each are known.
        source_col:
            Which column names the source endpoint. Worked out from the column
            names when it is not given.
        target_col:
            Which column names the target endpoint. Worked out from the column
            names when it is not given.
        directed_col:
            Which column says whether an edge is directed. A row that says
            nothing takes ``directed``.
        weight_col:
            Which column carries the weight of an edge. A row that says nothing
            weighs one.
        edge_id_col:
            Which column names an edge. The graph names the edge itself when no
            column does.
        slice_col:
            Which column places an edge in a slice, for a table that carries
            more than one condition.
        slice:
            The slice every edge goes into, where ``slice_col`` says nothing.
        directed:
            The direction an edge takes when the table does not state one.
        edge_attr_cols:
            Which columns become attributes of an edge. Every column that names
            no structure, by default.
        dropna:
            Skip a row that names no endpoint. Raise on one instead when False.
        **graph_kwargs:
            Passed to the AnnNet constructor.

    Returns:
        An ``annnet.AnnNet``.

    Raises:
        ImportError: If annnet is not installed.
        ValueError: If the endpoint columns cannot be worked out.

    Example::

        import omnipath_client as oc

        graph = oc.to_annnet(oc.relations(interaction_types='post_translational'))
        graph.ncount(), graph.ecount()
    """

    annnet = _require_annnet()
    columns, rows = _rows(df)

    source_col = source_col or _pick(columns, SOURCE_COLUMNS)
    target_col = target_col or _pick(columns, TARGET_COLUMNS)
    if source_col is None or target_col is None:
        raise ValueError(
            f'Could not tell which column names an endpoint. The table has '
            f'{columns!r}. Pass source_col and target_col.',
        )

    directed_col = directed_col or _pick(columns, DIRECTED_COLUMNS)
    weight_col = weight_col or _pick(columns, WEIGHT_COLUMNS)
    edge_id_col = edge_id_col or _pick(columns, EDGE_ID_COLUMNS)
    slice_col = slice_col or _pick(columns, SLICE_COLUMNS)

    if edge_attr_cols is None:
        structural = {
            source_col,
            target_col,
            directed_col,
            weight_col,
            edge_id_col,
            slice_col,
        }
        edge_attr_cols = [name for name in columns if name not in structural]

    logger.info(
        'Building a graph from %r and %r, with %d edge attributes',
        source_col,
        target_col,
        len(edge_attr_cols),
    )

    edges = []
    append = edges.append
    skipped = 0
    for row in rows:
        source = row.get(source_col)
        target = row.get(target_col)
        if _is_null(source) or _is_null(target):
            if not dropna:
                raise ValueError(
                    f'Row {len(edges) + skipped} names no endpoint, and dropna is False.',
                )
            skipped += 1
            continue

        weight = row.get(weight_col) if weight_col else None
        row_slice = slice
        if slice_col:
            stated = row.get(slice_col)
            if not _is_null(stated):
                row_slice = str(stated)

        append(
            {
                'source': str(source),
                'target': str(target),
                'weight': 1.0 if _is_null(weight) else float(weight),
                'edge_id': _as_edge_id(row.get(edge_id_col))
                if edge_id_col
                else None,
                'edge_directed': (
                    _as_bool(row.get(directed_col), directed)
                    if directed_col
                    else directed
                ),
                'slice': row_slice,
                'attributes': {
                    name: row.get(name)
                    for name in edge_attr_cols
                    if name in row
                },
            },
        )

    graph = annnet.AnnNet(directed=directed, **graph_kwargs)
    if edges:
        graph.add_edges(edges)

    logger.info(
        'Built a graph of %d nodes and %d edges, skipping %d rows with no endpoint',
        graph.ncount(),
        graph.ecount(),
        skipped,
    )
    return graph


def node_annotations(cache_dir: str | None = None) -> Any:
    """Return the OmniPath node annotation archive as a table.

    The archive is one large file. It is downloaded once and read from the
    cache after that, through the same download manager every other request of
    this package goes through.

    Args:
        cache_dir:
            Where to keep the archive. The cache of this package, by default.

    Returns:
        A polars ``LazyFrame`` over the archive, with the columns
        ``genesymbol``, ``source``, ``label`` and ``value``.

    Raises:
        ImportError: If polars is not installed.
    """

    try:
        import polars as pl
    except ImportError as error:
        raise ImportError(
            'polars is required to read the annotation archive. Install it with: '
            'pip install "omnipath-client[polars]"',
        ) from error

    from omnipath_client._download import Downloader

    path = Downloader(cache_dir=cache_dir)._download_url(ANNOTATIONS_URL)
    logger.info('Reading the node annotation archive from %s', path)
    return pl.scan_csv(path, separator='\t', has_header=True)


def annotate_nodes(
    graph: AnnNet,
    annotations: Any = None,
    *,
    sources: list[str] | None = None,
    cache_dir: str | None = None,
) -> AnnNet:
    """Give every node of a graph the annotations OmniPath holds for it.

    One node carries one value per ``source:label`` pair. A pair with several
    values carries them joined by a semicolon, in sorted order, so the value is
    the same however the rows arrived.

    Args:
        graph:
            The graph to annotate, changed in place and returned.
        annotations:
            The annotation table to read. Downloaded and cached when not given.
        sources:
            Which annotation resources to read. Every one, by default.
        cache_dir:
            Where to keep the downloaded archive.

    Returns:
        The same graph.

    Raises:
        ImportError: If polars is not installed.

    Example::

        import omnipath_client as oc

        graph = oc.to_annnet(oc.relations())
        oc.annotate_nodes(graph, sources=['HGNC', 'UniProt_location'])
    """

    import polars as pl

    frame = (
        node_annotations(cache_dir=cache_dir)
        if annotations is None
        else annotations
    )
    if not isinstance(frame, (pl.LazyFrame, pl.DataFrame)):
        # The filter below is a polars expression, and pushing it into a scan is
        # what keeps the archive off the heap. So a table on another backend is
        # read once, column by column, into a polars frame.
        import narwhals as nw

        columns = nw.from_native(frame, eager_only=True, pass_through=False)
        frame = pl.DataFrame(columns.to_dict(as_series=False))
    if isinstance(frame, pl.DataFrame):
        frame = frame.lazy()

    node_ids = list(graph.N)
    keep = (
        pl.col('genesymbol').is_in(node_ids)
        & pl.col('source').is_not_null()
        & pl.col('label').is_not_null()
        & pl.col('value').is_not_null()
    )
    if sources is not None:
        keep = keep & pl.col('source').is_in(list(sources))

    # The filter is pushed into the scan, so the archive is never held whole:
    # only the rows about nodes this graph has are read off the disk.
    aggregated = (
        frame.filter(keep)
        .select(
            pl.col('genesymbol'),
            (pl.col('source') + pl.lit(':') + pl.col('label')).alias(
                'attribute'
            ),
            pl.col('value').cast(pl.Utf8),
        )
        .group_by('genesymbol', 'attribute')
        .agg(pl.col('value').unique().sort().str.join(';').alias('joined'))
        .collect()
    )

    by_node: dict[str, dict[str, str]] = {}
    for genesymbol, attribute, joined in aggregated.iter_rows():
        by_node.setdefault(genesymbol, {})[attribute] = joined

    graph.attrs.set_vertex_attrs_bulk(by_node)
    logger.info(
        'Annotated %d of %d nodes with %d attribute pairs',
        len(by_node),
        len(node_ids),
        aggregated.height,
    )
    return graph
