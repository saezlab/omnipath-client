"""Base HTTP client for the utils service."""

from __future__ import annotations

from typing import Any
import logging

import requests


_log = logging.getLogger(__name__)

DEFAULT_UTILS_URL = 'https://utils.omnipathdb.org'

_utils_url: str = DEFAULT_UTILS_URL


def set_utils_url(url: str) -> None:
    """Set the base URL for the utils service."""

    global _utils_url
    _utils_url = url.rstrip('/')


def get_utils_url() -> str:
    """Get the current base URL."""

    return _utils_url


def _get(path: str, params: dict | None = None, timeout: int = 60) -> Any:
    """GET request to the utils service, returns parsed JSON."""

    url = f'{_utils_url}{path}'
    _log.debug('GET %s params=%s', url, params)
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()

    return resp.json()


def _post(path: str, data: dict, timeout: int = 120) -> Any:
    """POST request with JSON body."""

    url = f'{_utils_url}{path}'
    _log.debug('POST %s', url)
    resp = requests.post(url, json=data, timeout=timeout)
    resp.raise_for_status()

    return resp.json()
