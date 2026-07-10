"""Base HTTP client for the utils service.

Requests go through the dlmachine-backed :class:`omnipath_client.Downloader`,
so utils calls share the client's caching and detailed download logging
instead of issuing bare ``requests`` calls.
"""

from __future__ import annotations

from typing import Any
import os

from omnipath_client._download import Downloader
from omnipath_client._session import get_logger


_log = get_logger(__name__)

DEFAULT_UTILS_URL = 'https://utils.omnipathdb.org'
UTILS_URL_ENV_VAR = 'OMNIPATH_UTILS_URL'

_utils_url: str | None = None
_downloader: Downloader | None = None


def set_utils_url(url: str) -> None:
    """Set the base URL for the utils service (overrides the environment)."""

    global _utils_url
    _utils_url = url.rstrip('/')
    _log.info('Utils service URL set to %s', _utils_url)


def get_utils_url() -> str:
    """Return the current base URL for the utils service.

    Resolution order: an explicit :func:`set_utils_url`, the
    ``OMNIPATH_UTILS_URL`` environment variable, then the built-in default
    (``https://utils.omnipathdb.org``).
    """

    if _utils_url is not None:
        return _utils_url

    env_url = os.environ.get(UTILS_URL_ENV_VAR)

    if env_url:
        return env_url.rstrip('/')

    return DEFAULT_UTILS_URL


def _get_downloader() -> Downloader:
    """Return the shared, lazily created downloader for utils requests."""

    global _downloader

    if _downloader is None:
        _downloader = Downloader(use_cache=True)

    return _downloader


def _get(path: str, params: dict | None = None) -> Any:
    """GET request to the utils service, returns parsed JSON."""

    url = f'{get_utils_url()}{path}'
    _log.debug('GET %s params=%s', url, params)

    return _get_downloader().fetch_json(url, method='GET', params=params)


def _post(path: str, data: dict) -> Any:
    """POST request with a JSON body, returns parsed JSON."""

    url = f'{get_utils_url()}{path}'
    _log.debug('POST %s', url)

    return _get_downloader().fetch_json(url, method='POST', payload=data)
