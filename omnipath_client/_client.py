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

    def interactions(
        self,
        as_graph: bool = False,
        backend: BackendType | None = None,
        **filters: Any,
    ) -> Any:
        """Export interactions.

        Args:
            as_graph:
                If True, return an ``annnet.Graph`` instead of a
                DataFrame.
            backend:
                Override the default DataFrame backend.
            **filters:
                Filter parameters (entity_ids, interaction_types,
                direction, sign, etc.).

        Returns:
            A DataFrame of interactions, or an ``annnet.Graph``.
        """

        df = self._fetch(
            'exports/interactions/parquet',
            backend=backend,
            **filters,
        )

        if as_graph:
            from omnipath_client._graph import interactions_to_graph

            return interactions_to_graph(df)

        return df

    def associations(
        self,
        as_graph: bool = False,
        backend: BackendType | None = None,
        **filters: Any,
    ) -> Any:
        """Export associations (complexes, pathways, reactions).

        Args:
            as_graph:
                If True, return an ``annnet.Graph`` instead of a
                DataFrame.
            backend:
                Override the default DataFrame backend.
            **filters:
                Filter parameters (parent_entity_ids,
                member_entity_ids, etc.).

        Returns:
            A DataFrame of associations, or an ``annnet.Graph``.
        """

        df = self._fetch(
            'exports/associations/parquet',
            backend=backend,
            **filters,
        )

        if as_graph:
            from omnipath_client._graph import associations_to_graph

            return associations_to_graph(df)

        return df

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

    def interaction_evidence(self, interaction_id: int) -> Any:
        """Get full evidence for a single interaction.

        Args:
            interaction_id:
                The interaction ID.

        Returns:
            Evidence data as a dict.
        """

        return self._fetch(
            'interactions/{interaction_id}/evidence',
            interaction_id=interaction_id,
        )

    def association_evidence(self, association_id: int) -> Any:
        """Get full evidence for a single association.

        Args:
            association_id:
                The association ID.

        Returns:
            Evidence data as a dict.
        """

        return self._fetch(
            'associations/{association_id}/evidence',
            association_id=association_id,
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


def interactions(
    as_graph: bool = False,
    **filters: Any,
) -> Any:
    """Export interactions using the default client.

    See ``OmniPath.interactions`` for details.
    """

    return _get_default().interactions(as_graph=as_graph, **filters)


def associations(
    as_graph: bool = False,
    **filters: Any,
) -> Any:
    """Export associations using the default client.

    See ``OmniPath.associations`` for details.
    """

    return _get_default().associations(as_graph=as_graph, **filters)


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
