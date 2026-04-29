"""Main client: OmniPath class and module-level convenience functions."""

from __future__ import annotations

from typing import Any, Iterator, Sequence
from contextlib import contextmanager

from omnipath_client._pivot import (
    ID_ALIASES,
    DEFAULT_ID_TYPES,
    PARTICIPANT_TYPE_ALIASES,
    expand_aliases,
    pivot_identifiers,
    join_relations_with_entities,
)
from omnipath_client._query import QueryBuilder
from omnipath_client._types import BackendType
from omnipath_client._session import get_logger, get_session
from omnipath_client._download import Downloader
from omnipath_client._response import parse_response
from omnipath_client._constants import DEFAULT_BASE_URL
from omnipath_client._endpoints import ParamDef, EndpointDef
from omnipath_client._inventory import Inventory


logger = get_logger(__name__)


class OmniPath:
    """Client for the OmniPath web API.

    Args:
        base_url:
            Base URL of the OmniPath API.
        backend:
            Default DataFrame backend.
        cache:
            Whether to cache downloaded files.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        backend: BackendType = 'auto',
        cache: bool = True,
    ) -> None:

        get_session()

        self._base_url = base_url.rstrip('/')
        self._backend = backend
        self._inventory = Inventory(base_url=self._base_url)
        self._inventory.load()
        self._query_builder = QueryBuilder(self._inventory)
        self._downloader = Downloader(use_cache=cache)
        logger.info(
            'Initialized OmniPath client with base_url=%s backend=%s cache=%s',
            self._base_url,
            self._backend,
            cache,
        )

    def _fetch(
        self,
        endpoint: str,
        backend: BackendType | None = None,
        **params: Any,
    ) -> Any:
        """Internal: build query, download, parse response."""

        logger.info(
            'Starting request workflow for endpoint=%s backend=%s',
            endpoint,
            backend or self._backend,
        )
        query = self._query_builder.build(endpoint, **params)
        result = self._downloader.fetch(query)
        fmt = query.endpoint.response_format

        parsed = parse_response(
            result,
            response_format=fmt,
            backend=backend or self._backend,
        )

        logger.info(
            'Completed request workflow for endpoint=%s format=%s',
            endpoint,
            fmt,
        )

        return parsed

    # --- Export endpoints ---

    def entities(
        self,
        backend: BackendType | None = None,
        **filters: Any,
    ) -> Any:
        """Export entities.

        Args:
            backend:
                Override the default DataFrame backend.
            **filters:
                Filter parameters (entity_ids, entity_types,
                sources, taxonomy_ids, etc.).

        Returns:
            A DataFrame of entities.
        """

        return self._fetch(
            'exports/entities/parquet',
            backend=backend,
            **filters,
        )

    def relations(
        self,
        as_graph: bool = False,
        backend: BackendType | None = None,
        **filters: Any,
    ) -> Any:
        """Export relations (interactions, memberships, etc.).

        Args:
            as_graph:
                If True, return an ``annnet.Graph`` instead of a
                DataFrame.
            backend:
                Override the default DataFrame backend.
            **filters:
                Filter parameters (sources, predicates,
                interaction_types, relation_categories,
                subject_entity_pks, object_entity_pks, etc.).

        Returns:
            A DataFrame of relations, or an ``annnet.Graph``.
        """

        df = self._fetch(
            'exports/relations/parquet',
            backend=backend,
            **filters,
        )

        if as_graph:
            from omnipath_client._graph import relations_to_graph

            return relations_to_graph(df)

        return df

    def annotations(
        self,
        backend: BackendType | None = None,
        **filters: Any,
    ) -> Any:
        """Export ontology annotations attached to entities.

        Args:
            backend:
                Override the default DataFrame backend.
            **filters:
                Filter parameters (prefixes, ontology_prefixes,
                entity_pks).

        Returns:
            A DataFrame of annotations.
        """

        return self._fetch(
            'exports/annotations/parquet',
            backend=backend,
            **filters,
        )

    # --- Slice / lookup endpoints ---

    def resolve(self, identifiers: list[str]) -> Any:
        """Resolve free-text identifiers to entity primary keys.

        Args:
            identifiers:
                List of identifier strings (UniProt accessions,
                ChEBI IDs, gene symbols, free-text names, etc.).

        Returns:
            A dict with ``matches`` (per-input entity_pk lists) and
            ``entities`` (full entity records).
        """

        return self._fetch('entities/resolve', identifiers=identifiers)

    def entities_slice(
        self,
        filters: dict[str, Any] | None = None,
        query: str = '',
        limit: int = 50,
        offset: int = 0,
    ) -> Any:
        """Page through entities with filters and free-text search.

        Args:
            filters:
                ``EntityFilters`` payload (entity_pks, entity_types,
                sources, taxonomy_ids, ncbi_tax_id).
            query:
                Free-text search across canonical identifiers and
                aliases.
            limit:
                Maximum number of rows.
            offset:
                Row offset.

        Returns:
            A dict with ``rows``, ``total``, ``limit``, ``offset``.
        """

        return self._fetch(
            'entities/slice',
            filters=filters or {},
            query=query,
            limit=limit,
            offset=offset,
        )

    def relations_slice(
        self,
        filters: dict[str, Any] | None = None,
        query: str = '',
        limit: int = 50,
        offset: int = 0,
    ) -> Any:
        """Page through relations with filters and free-text search.

        Args:
            filters:
                ``RelationFilters`` payload (sources, predicates,
                relation_categories, subject_entity_pks, etc.).
            query:
                Free-text search.
            limit:
                Maximum number of rows.
            offset:
                Row offset.

        Returns:
            A dict with ``rows``, ``total``, ``limit``, ``offset``.
        """

        return self._fetch(
            'relations/slice',
            filters=filters or {},
            query=query,
            limit=limit,
            offset=offset,
        )

    def resources(self) -> Any:
        """List the resource catalog with build statistics.

        Returns:
            List of resource records (resource_id, resource_name,
            categories, entity_count, interaction_count, etc.).
        """

        return self._fetch('resources')

    # --- Ontology endpoints ---

    def ontology_terms(self, term_ids: list[str]) -> Any:
        """Batch lookup of ontology terms.

        Args:
            term_ids:
                List of term IDs (e.g. ``['GO:0006915']``).

        Returns:
            A dict with term information.
        """

        return self._fetch('terms', term_ids=term_ids)

    def ontology_tree(self, term_ids: list[str]) -> Any:
        """Get merged hierarchy tree for terms.

        Args:
            term_ids:
                List of term IDs.

        Returns:
            A tree structure dict.
        """

        return self._fetch('tree', term_ids=term_ids)

    def search_terms(
        self,
        queries: list[str],
        limit: int = 10,
    ) -> Any:
        """Search ontology terms by name or synonym.

        Args:
            queries:
                Search strings.
            limit:
                Maximum number of results per query.

        Returns:
            A dict with search results.
        """

        return self._fetch(
            'terms/search',
            queries=queries,
            limit=limit,
        )

    def ontologies(self) -> Any:
        """List all available ontologies.

        Returns:
            A dict with ontology information.
        """

        return self._fetch('ontologies')

    # --- Evidence endpoints ---

    def relation_evidence(self, relation_pk: int) -> Any:
        """Get full evidence for a single relation.

        Args:
            relation_pk:
                The relation primary key.

        Returns:
            Evidence data as a dict.
        """

        return self._fetch(
            'relations/{relation_pk}/evidence',
            relation_pk=relation_pk,
        )

    # --- High-level helpers ---

    def lookup(
        self,
        query: str | int | Sequence[str | int],
        id_types: Sequence[str] = DEFAULT_ID_TYPES,
        *,
        keep_canonical: bool = False,
    ) -> Any:
        """Resolve free-text or PK input and return enriched entity rows.

        Wraps ``resolve()`` + ``entities()`` and pivots the requested
        ``id_types`` into named columns.

        Args:
            query:
                A name, accession, or entity_pk; or a list of any
                combination thereof. Strings are auto-resolved.
            id_types:
                Aliases (or raw codes) to surface as columns. See
                ``omnipath_client._pivot.ID_ALIASES`` for the full
                alias map.
            keep_canonical:
                Retain ``canonical_identifier`` and the raw
                ``identifiers`` list-column.

        Returns:
            A polars DataFrame with one row per matched entity_pk.
        """

        items = [query] if isinstance(query, (str, int)) else list(query)
        names = [str(x) for x in items if not _is_int(x)]
        explicit_pks = [str(x) for x in items if _is_int(x)]

        resolved_pks: list[str] = list(explicit_pks)
        match_query: dict[int, list[str]] = {}

        if names:
            res = self.resolve(names)
            for m in res.get('matches', []):
                pks = [str(p) for p in m.get('entityPks', [])]
                resolved_pks.extend(pks)
                for p in pks:
                    match_query.setdefault(int(p), []).append(m['identifier'])

        if not resolved_pks:
            ents = self.entities(entity_pks=['__none__'])
            return pivot_identifiers(
                ents,
                id_types=id_types,
                keep_canonical=keep_canonical,
            )

        ents = self.entities(entity_pks=list(dict.fromkeys(resolved_pks)))
        wide = pivot_identifiers(
            ents,
            id_types=id_types,
            keep_canonical=keep_canonical,
        )

        if match_query:
            import polars as pl

            mapping = pl.DataFrame(
                {
                    'entity_pk': list(match_query),
                    'query': [
                        ', '.join(sorted(set(v)))
                        for v in match_query.values()
                    ],
                },
            )
            wide = mapping.join(wide, on='entity_pk', how='right')

        return wide

    def related(
        self,
        query: str | int | Sequence[str | int] | None = None,
        *,
        subject: str | int | Sequence[str | int] | None = None,
        object: str | int | Sequence[str | int] | None = None,
        sources: Sequence[str] | None = None,
        predicates: Sequence[str] | None = None,
        relation_categories: Sequence[str] | None = None,
        participant_types: Sequence[str] | None = None,
        id_types: Sequence[str] = DEFAULT_ID_TYPES,
        group_by: str | None = None,
        limit: int | None = None,
        keep_canonical: bool = False,
    ) -> Any:
        """Pull joined relations around a query in one call.

        Resolves any string inputs, fetches the matching relations,
        fetches the entity records for every involved PK, and joins
        them back into a wide DataFrame with ``subject_*`` / ``object_*``
        columns.

        Args:
            query:
                Positional argument matching the entity on **either**
                side of the relation. Use ``subject=`` / ``object=`` to
                pin a direction.
            subject:
                Restrict to relations where this entity is the subject.
            object:
                Restrict to relations where this entity is the object.
            sources:
                Resource IDs to include (e.g. ``['foodb', 'hmdb']``).
            predicates:
                Predicate filter (e.g. ``['has_member']``).
            relation_categories:
                Category filter (``['interaction', 'membership',
                'annotation']``).
            participant_types:
                Friendly aliases (``'protein'``, ``'small_molecule'``,
                …) or raw MI codes.
            id_types:
                Identifier aliases to pivot as ``subject_<id>`` and
                ``object_<id>`` columns.
            group_by:
                Sort the result by this column (e.g.
                ``'object_canonical_id'``); useful when the same
                entity appears under several pathway IDs.
            limit:
                Truncate the output to this many rows.
            keep_canonical:
                Retain canonical_identifier / raw identifiers columns.

        Returns:
            A wide polars DataFrame.
        """

        subj_pks = self._resolve_to_pks(subject if subject is not None else query)
        obj_pks = self._resolve_to_pks(object) if object is not None else None

        rel_filters: dict[str, Any] = {}

        if sources:
            rel_filters['sources'] = list(sources)
        if predicates:
            rel_filters['predicates'] = list(predicates)
        if relation_categories:
            rel_filters['relation_categories'] = list(relation_categories)
        if participant_types:
            rel_filters['participant_types'] = expand_aliases(
                participant_types, PARTICIPANT_TYPE_ALIASES,
            )

        # Direction handling: when only the positional ``query`` was
        # given, match either side; when ``subject``/``object`` were
        # passed, pin them.
        if subject is not None and obj_pks is not None:
            rel_filters['subject_entity_pks'] = subj_pks
            rel_filters['object_entity_pks'] = obj_pks
        elif subject is not None:
            rel_filters['subject_entity_pks'] = subj_pks
        elif object is not None:
            rel_filters['object_entity_pks'] = obj_pks
        elif subj_pks is not None:
            rel_filters['entity_pks'] = subj_pks

        rel_df = self.relations(**rel_filters)

        if rel_df.height == 0:
            return rel_df

        import polars as pl

        all_pks = (
            pl.concat([
                rel_df.select(pl.col('subject_entity_pk').alias('pk')),
                rel_df.select(pl.col('object_entity_pk').alias('pk')),
            ])
            .unique()
            .drop_nulls()
            ['pk']
            .to_list()
        )

        ent_df = self.entities(entity_pks=[str(p) for p in all_pks])

        out = join_relations_with_entities(
            rel_df, ent_df,
            id_types=id_types,
            keep_canonical=keep_canonical,
        )

        if group_by and group_by in out.columns:
            out = out.sort(group_by)
        if limit is not None:
            out = out.head(limit)

        return out

    def _resolve_to_pks(
        self,
        x: str | int | Sequence[str | int] | None,
    ) -> list[str] | None:
        if x is None:
            return None

        items = [x] if isinstance(x, (str, int)) else list(x)
        out: list[str] = []
        names: list[str] = []

        for item in items:
            if _is_int(item):
                out.append(str(item))
            else:
                names.append(str(item))

        if names:
            res = self.resolve(names)
            for m in res.get('matches', []):
                out.extend(str(p) for p in m.get('entityPks', []))

        return list(dict.fromkeys(out)) or None

    # --- Cache management ---

    def cache_clear(self) -> int:
        """Remove every cached response (incl. the cached OpenAPI
        spec). Returns the number of entries removed."""

        n = self._downloader.clear_cache()
        # Drop the in-process inventory copy so the next call refetches.
        self._inventory.load()
        return n

    @contextmanager
    def fresh(self) -> Iterator[None]:
        """Context manager that re-downloads any response touched
        within the block on first use, then serves subsequent
        identical requests from the freshly populated cache.

        Example::

            with client.fresh():
                df = client.related('caffeine', sources=['bindingdb'])
        """

        self._downloader.enter_fresh()
        try:
            yield
        finally:
            self._downloader.exit_fresh()

    # --- Introspection ---

    @property
    def endpoint_registry(self) -> dict[str, EndpointDef]:
        """All registered endpoints."""

        return self._inventory.endpoints

    def params(self, endpoint: str) -> dict[str, ParamDef]:
        """Parameters for an endpoint."""

        return self._inventory.params(endpoint)

    def values(
        self,
        endpoint: str,
        param: str,
    ) -> list[str] | None:
        """Allowed values for a parameter on an endpoint."""

        return self._inventory.allowed_values(endpoint, param)


def _is_int(x: Any) -> bool:
    if isinstance(x, bool):
        return False
    if isinstance(x, int):
        return True
    if isinstance(x, str):
        return x.lstrip('-').isdigit()
    return False


# --- Module-level convenience API via lazy default singleton ---

_default_client: OmniPath | None = None


def _get_default() -> OmniPath:
    """Get or create the default client singleton."""

    global _default_client

    if _default_client is None:
        logger.info('Creating default OmniPath client singleton')
        _default_client = OmniPath()

    return _default_client


def entities(**filters: Any) -> Any:
    """Export entities using the default client.

    See ``OmniPath.entities`` for details.
    """

    return _get_default().entities(**filters)


def relations(
    as_graph: bool = False,
    **filters: Any,
) -> Any:
    """Export relations using the default client.

    See ``OmniPath.relations`` for details.
    """

    return _get_default().relations(as_graph=as_graph, **filters)


def annotations(**filters: Any) -> Any:
    """Export ontology annotations using the default client.

    See ``OmniPath.annotations`` for details.
    """

    return _get_default().annotations(**filters)


def resolve(identifiers: list[str]) -> Any:
    """Resolve identifiers using the default client.

    See ``OmniPath.resolve`` for details.
    """

    return _get_default().resolve(identifiers)


def entities_slice(
    filters: dict[str, Any] | None = None,
    query: str = '',
    limit: int = 50,
    offset: int = 0,
) -> Any:
    """Slice entities using the default client.

    See ``OmniPath.entities_slice`` for details.
    """

    return _get_default().entities_slice(
        filters=filters,
        query=query,
        limit=limit,
        offset=offset,
    )


def relations_slice(
    filters: dict[str, Any] | None = None,
    query: str = '',
    limit: int = 50,
    offset: int = 0,
) -> Any:
    """Slice relations using the default client.

    See ``OmniPath.relations_slice`` for details.
    """

    return _get_default().relations_slice(
        filters=filters,
        query=query,
        limit=limit,
        offset=offset,
    )


def resources() -> Any:
    """List resources catalog using the default client.

    See ``OmniPath.resources`` for details.
    """

    return _get_default().resources()


def ontology_terms(term_ids: list[str]) -> Any:
    """Batch lookup of ontology terms using the default client.

    See ``OmniPath.ontology_terms`` for details.
    """

    return _get_default().ontology_terms(term_ids)


def ontology_tree(term_ids: list[str]) -> Any:
    """Get merged hierarchy tree using the default client.

    See ``OmniPath.ontology_tree`` for details.
    """

    return _get_default().ontology_tree(term_ids)


def search_terms(queries: list[str], limit: int = 10) -> Any:
    """Search ontology terms using the default client.

    See ``OmniPath.search_terms`` for details.
    """

    return _get_default().search_terms(queries, limit)


def ontologies() -> Any:
    """List ontologies using the default client.

    See ``OmniPath.ontologies`` for details.
    """

    return _get_default().ontologies()


def endpoints() -> dict[str, EndpointDef]:
    """List all available API endpoints.

    Returns:
        Dict mapping endpoint paths to EndpointDef objects.

    Example::

        import omnipath_client as op
        for path, ep in op.endpoints().items():
            print(f'{ep.method} {path}: {ep.summary}')
    """

    return _get_default().endpoint_registry


def params(endpoint: str) -> dict[str, ParamDef]:
    """Get parameters for an endpoint.

    Args:
        endpoint: Endpoint path (e.g. 'exports/relations/parquet').

    Returns:
        Dict mapping parameter names to ParamDef objects with
        name, type, required, allowed_values, and description.

    Example::

        import omnipath_client as op
        for name, p in op.params('exports/relations/parquet').items():
            vals = p.allowed_values or []
            print(f'{name}: {p.param_type}, required={p.required}, values={vals[:5]}')
    """

    return _get_default().params(endpoint)


def values(endpoint: str, param: str) -> list[str] | None:
    """Get allowed values for a parameter on an endpoint.

    Args:
        endpoint: Endpoint path.
        param: Parameter name.

    Returns:
        List of allowed values, or None if any value is accepted.

    Example::

        import omnipath_client as op
        op.values('exports/entities/parquet', 'entity_types')
        # ['MI:0326:Protein', 'MI:0328:Small Molecule', ...]
    """

    return _get_default().values(endpoint, param)


def lookup(
    query: str | int | Sequence[str | int],
    id_types: Sequence[str] = DEFAULT_ID_TYPES,
    *,
    keep_canonical: bool = False,
) -> Any:
    """Resolve and enrich entities using the default client.

    See ``OmniPath.lookup`` for details.
    """

    return _get_default().lookup(
        query,
        id_types=id_types,
        keep_canonical=keep_canonical,
    )


def related(
    query: str | int | Sequence[str | int] | None = None,
    *,
    subject: str | int | Sequence[str | int] | None = None,
    object: str | int | Sequence[str | int] | None = None,
    sources: Sequence[str] | None = None,
    predicates: Sequence[str] | None = None,
    relation_categories: Sequence[str] | None = None,
    participant_types: Sequence[str] | None = None,
    id_types: Sequence[str] = DEFAULT_ID_TYPES,
    group_by: str | None = None,
    limit: int | None = None,
    keep_canonical: bool = False,
) -> Any:
    """Pull joined relations around a query using the default client.

    See ``OmniPath.related`` for details.
    """

    return _get_default().related(
        query,
        subject=subject,
        object=object,
        sources=sources,
        predicates=predicates,
        relation_categories=relation_categories,
        participant_types=participant_types,
        id_types=id_types,
        group_by=group_by,
        limit=limit,
        keep_canonical=keep_canonical,
    )


def cache_clear() -> int:
    """Clear the on-disk cache for the default client. Returns the
    number of entries removed."""

    return _get_default().cache_clear()


@contextmanager
def fresh() -> Iterator[None]:
    """Context manager that re-downloads any responses touched within
    the block (first-touch refresh, then served from the freshly
    populated cache).

    Example::

        import omnipath_client as oc
        with oc.fresh():
            df = oc.related('caffeine', sources=['bindingdb'])
    """

    with _get_default().fresh():
        yield
