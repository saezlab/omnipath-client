"""Query builder with validation against the API inventory."""

from __future__ import annotations

from typing import Any
from dataclasses import field, dataclass

from omnipath_client._errors import (
    UnknownEndpointError,
    UnknownParameterError,
    InvalidParameterValueError,
)
from omnipath_client._session import get_logger
from omnipath_client._endpoints import EndpointDef
from omnipath_client._inventory import Inventory


logger = get_logger(__name__)


@dataclass
class Query:
    """A validated query for an OmniPath API endpoint."""

    endpoint: EndpointDef
    params: dict[str, Any] = field(default_factory=dict)
    base_url: str = ''

    @property
    def url(self) -> str:
        """Full URL for this query."""

        return f'{self.base_url}{self.endpoint.path}'

    @property
    def json_body(self) -> dict[str, Any] | None:
        """JSON request body for POST endpoints.

        Returns None for GET endpoints.
        """

        if self.endpoint.method != 'POST':
            return None

        # Separate filter params from top-level params
        filters = {}
        top_level = {}

        for name, value in self.params.items():
            pdef = self.endpoint.params.get(name)

            if pdef and pdef.location == 'filter':
                filters[name] = value
            else:
                top_level[name] = value

        # Build the request body
        body: dict[str, Any] = {}

        if top_level:
            body.update(top_level)

        if filters:
            body['filters'] = filters

        logger.debug(
            'Built JSON body for %s with top-level keys=%s and filter keys=%s',
            self.endpoint.path,
            sorted(top_level.keys()),
            sorted(filters.keys()),
        )

        return body

    @property
    def query_params(self) -> dict[str, Any]:
        """URL query parameters for GET endpoints.

        Returns an empty dict for POST endpoints.
        """

        if self.endpoint.method != 'GET':
            return {}

        logger.debug(
            'Using query parameters for %s: %s',
            self.endpoint.path,
            sorted(self.params.keys()),
        )

        return dict(self.params)

    @property
    def path_params(self) -> dict[str, Any]:
        """Path parameters extracted from the query params."""

        result = {}

        for name, pdef in self.endpoint.params.items():
            if pdef.location == 'path' and name in self.params:
                result[name] = self.params[name]

        return result

    @property
    def resolved_url(self) -> str:
        """URL with path parameters substituted."""

        url = self.url

        for name, value in self.path_params.items():
            url = url.replace(f'{{{name}}}', str(value))

        return url


class QueryBuilder:
    """Builds and validates queries against the API inventory."""

    def __init__(self, inventory: Inventory) -> None:

        self._inventory = inventory
        logger.debug(
            'Initialized QueryBuilder with %d known endpoints',
            len(self._inventory.endpoints),
        )

    def build(
        self,
        endpoint: str,
        **params: Any,
    ) -> Query:
        """Build a validated query.

        Args:
            endpoint:
                The endpoint key, e.g.
                ``'exports/interactions/parquet'``.
            **params:
                Query parameters.

        Returns:
            A validated ``Query`` instance.

        Raises:
            UnknownEndpointError:
                If the endpoint is not in the inventory.
            UnknownParameterError:
                If a parameter is not recognized.
            InvalidParameterValueError:
                If a value is not in the allowed set.
        """

        logger.info(
            'Building query for endpoint %s with parameters=%s',
            endpoint,
            sorted(params.keys()),
        )

        ep = self._inventory.endpoints.get(endpoint)

        if ep is None:
            logger.error('Unknown endpoint requested: %s', endpoint)
            raise UnknownEndpointError(
                f'Unknown endpoint: {endpoint!r}. '
                f'Available: {list(self._inventory.endpoints.keys())}',
            )

        validated: dict[str, Any] = {}

        for name, value in params.items():
            if value is None:
                continue

            pdef = ep.params.get(name)

            if pdef is None:
                logger.error(
                    'Unknown parameter %s for endpoint %s',
                    name,
                    endpoint,
                )
                raise UnknownParameterError(
                    f'Unknown parameter {name!r} for endpoint '
                    f'{endpoint!r}. '
                    f'Available: {list(ep.params.keys())}',
                )

            # Validate enum values
            if pdef.allowed_values is not None:
                check = value if isinstance(value, str) else str(value)

                if check not in pdef.allowed_values:
                    logger.error(
                        'Invalid value %r for parameter %s on endpoint %s',
                        value,
                        name,
                        endpoint,
                    )
                    raise InvalidParameterValueError(
                        f'Invalid value {value!r} for parameter '
                        f'{name!r}. '
                        f'Allowed: {pdef.allowed_values}',
                    )

            validated[name] = value

        logger.info(
            'Validated query for endpoint %s with %d parameter(s)',
            endpoint,
            len(validated),
        )

        return Query(
            endpoint=ep,
            params=validated,
            base_url=self._inventory._base_url,
        )
