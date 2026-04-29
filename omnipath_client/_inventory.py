"""API inventory: fetches and parses the OpenAPI schema from the server.

Populates endpoint definitions, parameter schemas, and allowed values.
Loaded at import time; failure never blocks import.
"""

from __future__ import annotations

from typing import Any

from omnipath_client._session import get_logger
from omnipath_client._constants import (
    OPENAPI_PATH,
    DEFAULT_BASE_URL,
    STATIC_ENDPOINTS,
)
from omnipath_client._endpoints import ParamDef, EndpointDef


logger = get_logger(__name__)


def _param_type_from_schema(schema: dict) -> str:
    """Derive a parameter type string from an OpenAPI property schema."""

    if 'enum' in schema:
        return 'enum'

    schema_type = schema.get('type')

    if schema_type == 'array':
        return 'array[string]'

    if schema_type == 'boolean':
        return 'boolean'

    if schema_type == 'integer':
        return 'integer'

    # Handle anyOf (nullable types)
    any_of = schema.get('anyOf', [])

    for variant in any_of:
        if variant.get('type') == 'string' and 'enum' in variant:
            return 'enum'

        if variant.get('type') == 'boolean':
            return 'boolean'

        if variant.get('type') == 'string':
            return 'string'

    return 'string'


def _allowed_values_from_schema(schema: dict) -> list[str] | None:
    """Extract allowed enum values from an OpenAPI property schema."""

    if 'enum' in schema:
        return schema['enum']

    for variant in schema.get('anyOf', []):
        if 'enum' in variant:
            return variant['enum']

    return None


def _parse_filters_schema(
    schema_name: str,
    schemas: dict[str, Any],
) -> dict[str, ParamDef]:
    """Parse a filters schema into ParamDef instances."""

    schema = schemas.get(schema_name, {})
    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    params = {}

    for name, prop in properties.items():
        params[name] = ParamDef(
            name=name,
            param_type=_param_type_from_schema(prop),
            required=name in required,
            allowed_values=_allowed_values_from_schema(prop),
            description=prop.get('description', ''),
            location='filter',
        )

    return params


def _parse_request_schema(
    schema_name: str,
    schemas: dict[str, Any],
) -> dict[str, ParamDef]:
    """Parse a request schema into ParamDef instances.

    For export endpoints, this extracts the filters sub-schema.
    For other POST endpoints, this extracts top-level properties.
    """

    schema = schemas.get(schema_name, {})
    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    params: dict[str, ParamDef] = {}

    for name, prop in properties.items():
        # If this property references a filters schema, expand it
        ref = prop.get('$ref', '')

        if ref and 'Filters' in ref:
            filters_name = ref.rsplit('/', 1)[-1]
            params.update(_parse_filters_schema(filters_name, schemas))
            continue

        # Skip the 'filename' field — internal to the API
        if name == 'filename':
            continue

        params[name] = ParamDef(
            name=name,
            param_type=_param_type_from_schema(prop),
            required=name in required,
            allowed_values=_allowed_values_from_schema(prop),
            description=prop.get('description', ''),
            location='body',
        )

    return params


def _response_format_from_path(path: str) -> str:
    """Infer the response format from the endpoint path."""

    if path.endswith('/parquet'):
        return 'parquet'

    return 'json'


def parse_openapi(spec: dict[str, Any]) -> dict[str, EndpointDef]:
    """Parse an OpenAPI 3.x spec dict into endpoint definitions.

    Args:
        spec:
            Parsed OpenAPI JSON as a dict.

    Returns:
        A dict mapping endpoint keys to ``EndpointDef`` instances.
    """

    schemas = spec.get('components', {}).get('schemas', {})
    paths = spec.get('paths', {})
    endpoints: dict[str, EndpointDef] = {}

    logger.debug(
        'Parsing OpenAPI spec with %d path(s) and %d schema(s)',
        len(paths),
        len(schemas),
    )

    # When the same path is exposed under multiple verbs, prefer
    # the POST variant — its JSON body carries the structured
    # filter parameters, while the GET variant degrades them to
    # opaque query strings.
    _method_priority = {'POST': 3, 'PUT': 2, 'GET': 1, 'DELETE': 0}

    for path, methods in paths.items():
        ordered = sorted(
            methods.items(),
            key=lambda kv: _method_priority.get(kv[0].upper(), -1),
        )

        for method, details in ordered:
            key = path.lstrip('/')
            params: dict[str, ParamDef] = {}

            # Parse path and query parameters
            for param in details.get('parameters', []):
                param_schema = param.get('schema', {})

                params[param['name']] = ParamDef(
                    name=param['name'],
                    param_type=_param_type_from_schema(param_schema),
                    required=param.get('required', False),
                    allowed_values=_allowed_values_from_schema(
                        param_schema,
                    ),
                    description=param.get('description', ''),
                    location=param.get('in', 'query'),
                )

            # Parse request body schema
            body = details.get('requestBody', {})
            body_content = body.get('content', {})
            json_schema = body_content.get(
                'application/json',
                {},
            ).get('schema', {})
            ref = json_schema.get('$ref', '')

            if ref:
                schema_name = ref.rsplit('/', 1)[-1]
                params.update(
                    _parse_request_schema(schema_name, schemas),
                )

            endpoints[key] = EndpointDef(
                path=path,
                method=method.upper(),
                summary=details.get('summary', ''),
                description=details.get('description', ''),
                response_format=_response_format_from_path(path),
                params=params,
                request_schema=ref.rsplit('/', 1)[-1] if ref else None,
            )

    return endpoints


def _build_static_fallback() -> dict[str, EndpointDef]:
    """Build endpoint definitions from the static fallback constants."""

    endpoints: dict[str, EndpointDef] = {}

    for key, data in STATIC_ENDPOINTS.items():
        params: dict[str, ParamDef] = {}

        for name, pdef in data.get('filters', {}).items():
            params[name] = ParamDef(
                name=name,
                param_type=pdef.get('type', 'string'),
                allowed_values=pdef.get('allowed'),
                location='filter',
            )

        for name, pdef in data.get('params', {}).items():
            params[name] = ParamDef(
                name=name,
                param_type=pdef.get('type', 'string'),
                required=pdef.get('required', False),
                location='body',
            )

        endpoints[key] = EndpointDef(
            path=data['path'],
            method=data['method'],
            summary=data.get('summary', ''),
            response_format=data.get('response_format', 'json'),
            params=params,
        )

    return endpoints


class Inventory:
    """Registry of all known API endpoints and parameters.

    Fetches the OpenAPI schema from the server and parses it into
    endpoint definitions. Falls back to static definitions on failure.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: bool = False,
    ) -> None:

        self._base_url = base_url.rstrip('/')
        self._cache = cache
        self._endpoints: dict[str, EndpointDef] = {}
        self._loaded = False
        logger.debug(
            'Created inventory for base_url=%s cache=%s',
            self._base_url,
            self._cache,
        )

    def load(self, force_refresh: bool = False) -> None:
        """Load the inventory from the server or static fallback.

        Args:
            force_refresh:
                If True, bypass any cached inventory and re-fetch.
        """

        if self._loaded and not force_refresh:
            logger.debug(
                'Inventory already loaded for %s; skipping refresh',
                self._base_url,
            )
            return

        try:
            self._load_from_server(force_refresh=force_refresh)

        except Exception:  # noqa: BLE001
            logger.warning(
                'Failed to load API schema from %s, using static fallback',
                self._base_url,
                exc_info=True,
            )
            self._endpoints = _build_static_fallback()
            logger.info(
                'Loaded %d endpoints from static fallback',
                len(self._endpoints),
            )

        self._loaded = True

    def _load_from_server(
        self,
        force_refresh: bool = False,
    ) -> None:
        """Fetch and parse the OpenAPI schema from the server."""

        url = f'{self._base_url}{OPENAPI_PATH}'
        logger.info('Fetching API schema from %s', url)

        from omnipath_client._download import Downloader

        downloader = Downloader(use_cache=self._cache)
        data = downloader.fetch_json(
            url,
            force_download=force_refresh,
        )

        self._endpoints = parse_openapi(data)
        logger.info(
            'Loaded %d endpoints from API schema',
            len(self._endpoints),
        )

    @property
    def endpoints(self) -> dict[str, EndpointDef]:
        """All registered endpoints."""

        if not self._loaded:
            logger.debug(
                'Inventory access triggered lazy load for %s',
                self._base_url,
            )
            self.load()

        return self._endpoints

    def params(self, endpoint: str) -> dict[str, ParamDef]:
        """Parameters for a given endpoint.

        Args:
            endpoint:
                The endpoint key, e.g.
                ``'exports/interactions/parquet'``.

        Returns:
            A dict mapping parameter names to ``ParamDef`` instances.
        """

        ep = self.endpoints.get(endpoint)

        if ep is None:
            return {}

        return ep.params

    def allowed_values(
        self,
        endpoint: str,
        param: str,
    ) -> list[str] | None:
        """Allowed values for a parameter on an endpoint.

        Args:
            endpoint:
                The endpoint key.
            param:
                The parameter name.

        Returns:
            A list of allowed values, or ``None`` if unconstrained.
        """

        params = self.params(endpoint)
        pdef = params.get(param)

        if pdef is None:
            return None

        return pdef.allowed_values
