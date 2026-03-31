"""Exception hierarchy for omnipath-client."""


class OmniPathError(Exception):
    """Base exception for all omnipath-client errors."""


class OmniPathAPIError(OmniPathError):
    """Error returned by the OmniPath API (HTTP 4xx/5xx)."""

    def __init__(self, status_code: int, detail: str = '') -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'HTTP {status_code}: {detail}')


class OmniPathConnectionError(OmniPathError):
    """Network or connection error when contacting the API."""


class QueryValidationError(OmniPathError):
    """Base for query parameter validation errors."""


class UnknownEndpointError(QueryValidationError):
    """The requested endpoint is not in the inventory."""


class UnknownParameterError(QueryValidationError):
    """A parameter name is not recognized for the endpoint."""


class InvalidParameterValueError(QueryValidationError):
    """A parameter value is not in the set of allowed values."""


class MissingParameterError(QueryValidationError):
    """A required parameter was not provided."""


class BackendNotAvailableError(OmniPathError):
    """The requested DataFrame backend is not installed."""
