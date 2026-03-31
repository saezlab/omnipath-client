"""Query builder with validation against the API inventory."""

from __future__ import annotations

from typing import Any
import logging
from dataclasses import field, dataclass

from omnipath_client._errors import (
    UnknownEndpointError,
    UnknownParameterError,
    InvalidParameterValueError,
)
from omnipath_client._endpoints import EndpointDef
from omnipath_client._inventory import Inventory


logger = logging.getLogger(__name__)


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

        return body

    @property
    def query_params(self) -> dict[str, Any]:
        """URL query parameters for GET endpoints.

        Returns an empty dict for POST endpoints.
        """

        if self.endpoint.method != 'GET':
            return {}

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

        ep = self._inventory.endpoints.get(endpoint)

        if ep is None:
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
                raise UnknownParameterError(
                    f'Unknown parameter {name!r} for endpoint '
                    f'{endpoint!r}. '
                    f'Available: {list(ep.params.keys())}',
                )

            # Validate enum values
            if pdef.allowed_values is not None:
                check = value if isinstance(value, str) else str(value)

                if check not in pdef.allowed_values:
                    raise InvalidParameterValueError(
                        f'Invalid value {value!r} for parameter '
                        f'{name!r}. '
                        f'Allowed: {pdef.allowed_values}',
                    )

            validated[name] = value

        return Query(
            endpoint=ep,
            params=validated,
            base_url=self._inventory._base_url,
        )
