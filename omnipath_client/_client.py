"""Main client: OmniPath class and module-level convenience functions."""

from __future__ import annotations

from typing import Any

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
