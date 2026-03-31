"""Download layer wrapping download-manager for API requests."""

from __future__ import annotations

import io
from typing import Any
import logging
from pathlib import Path

from omnipath_client._query import Query
from omnipath_client._errors import (
    OmniPathAPIError,
    OmniPathConnectionError,
)


logger = logging.getLogger(__name__)


class Downloader:
    """Handles downloads from the OmniPath API with caching.

    Uses ``download_manager.DownloadManager`` for HTTP requests and
    ``cache_manager`` for local caching of responses.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        use_cache: bool = True,
    ) -> None:

        from download_manager import DownloadManager

        dm_kwargs: dict[str, Any] = {}

        if cache_dir:
            dm_kwargs['path'] = str(cache_dir)
        elif use_cache:
            dm_kwargs['pkg'] = 'omnipath_client'

        self._dm = DownloadManager(**dm_kwargs)
        self._use_cache = use_cache

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

        url = query.resolved_url
        method = query.endpoint.method

        try:
            dl_kwargs: dict[str, Any] = {}

            if method == 'POST':
                dl_kwargs['post'] = True
                dl_kwargs['json'] = True
                dl_kwargs['query'] = query.json_body or {}
            elif query.query_params:
                dl_kwargs['query'] = query.query_params

            dest = None if self._use_cache else False
            result = self._dm.download(url, dest=dest, **dl_kwargs)

        except Exception as e:
            raise OmniPathConnectionError(
                f'Failed to download from {url}: {e}',
            ) from e

        # Check for HTTP errors via the downloader's state
        if hasattr(self._dm, '_last_downloader'):
            dl = self._dm._last_downloader

            if hasattr(dl, 'http_code') and dl.http_code >= 400:
                raise OmniPathAPIError(
                    status_code=dl.http_code,
                    detail=f'Request to {url} failed',
                )

        if result is None:
            raise OmniPathConnectionError(
                f'Download returned None for {url}',
            )

        return result
