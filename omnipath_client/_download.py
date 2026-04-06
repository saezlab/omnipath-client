"""Download layer wrapping download-manager for API requests."""

from __future__ import annotations

import io
import json
from typing import Any
from pathlib import Path

from omnipath_client._query import Query
from omnipath_client._errors import (
    OmniPathAPIError,
    OmniPathConnectionError,
)
from omnipath_client._session import get_logger


logger = get_logger(__name__)


class Downloader:
    """Handles downloads from the OmniPath API with caching.

    Uses ``dlmachine.DownloadManager`` for HTTP requests and
    ``cachedir`` for local caching of responses.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        use_cache: bool = True,
    ) -> None:

        from dlmachine import DownloadManager

        dm_kwargs: dict[str, Any] = {}

        if cache_dir:
            dm_kwargs['path'] = str(cache_dir)
        elif use_cache:
            dm_kwargs['pkg'] = 'omnipath_client'

        self._dm = DownloadManager(**dm_kwargs)
        self._use_cache = use_cache
        logger.info(
            'Initialized downloader with cache=%s cache_dir=%s',
            use_cache,
            cache_dir,
        )

    def _download_url(
        self,
        url: str,
        *,
        method: str = 'GET',
        payload: dict[str, Any] | None = None,
        force_download: bool = False,
    ) -> str | io.BytesIO:
        """Download data from a URL using the configured cache policy."""

        logger.info(
            'Fetching %s %s with parameter keys=%s',
            method,
            url,
            sorted(payload.keys()) if payload else [],
        )

        try:
            dl_kwargs: dict[str, Any] = {}

            if method == 'POST':
                dl_kwargs['post'] = True
                dl_kwargs['json'] = True
                dl_kwargs['query'] = payload or {}
            elif payload:
                dl_kwargs['query'] = payload

            dest = None if self._use_cache else False
            result = self._dm.download(
                url,
                dest=dest,
                force_download=force_download,
                **dl_kwargs,
            )

        except Exception as e:
            message = f'Failed to download from {url}: {e}'
            logger.exception(message)
            raise OmniPathConnectionError(message) from e

        if hasattr(self._dm, '_last_downloader'):
            dl = self._dm._last_downloader

            if hasattr(dl, 'http_code') and dl.http_code >= 400:
                logger.error(
                    'HTTP error while fetching %s: status_code=%s',
                    url,
                    dl.http_code,
                )
                raise OmniPathAPIError(
                    status_code=dl.http_code,
                    detail=f'Request to {url} failed',
                )

        if result is None:
            logger.error('Downloader returned no data for %s', url)
            raise OmniPathConnectionError(
                f'Download returned None for {url}',
            )

        logger.info(
            'Fetched response for %s into %s',
            url,
            type(result).__name__,
        )

        return result

    def fetch(self, query: Query) -> str | io.BytesIO:
        """Download the response for a query.

        Args:
            query:
                A validated ``Query`` instance.

        Returns:
            Path to a cached file (str), or an in-memory buffer
            (``io.BytesIO``) if caching is disabled.

        Raises:
            OmniPathAPIError:
                If the server returns an error status.
            OmniPathConnectionError:
                If the connection fails.
        """

        method = query.endpoint.method
        payload = query.json_body if method == 'POST' else query.query_params

        return self._download_url(
            query.resolved_url,
            method=method,
            payload=payload,
        )

    def fetch_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        force_download: bool = False,
    ) -> Any:
        """Download and decode a JSON response."""

        result = self._download_url(
            url,
            method='GET',
            payload=params,
            force_download=force_download,
        )

        if isinstance(result, io.BytesIO):
            raw = result.getvalue()
        else:
            raw = Path(result).read_bytes()

        try:
            return json.loads(raw.decode('utf-8'))

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            message = f'Failed to decode JSON from {url}: {e}'
            logger.exception(message)
            raise OmniPathConnectionError(message) from e
