"""Response parsing and DataFrame backend conversion."""

from __future__ import annotations

import io
from typing import Any
import logging
from pathlib import Path

from omnipath_client._types import BackendType, ResponseFormat
from omnipath_client._errors import BackendNotAvailableError


logger = logging.getLogger(__name__)

# Backend preference order for auto-detection
_BACKEND_ORDER = ('polars', 'pyarrow', 'pandas')

_PARQUET_READERS = {
    'polars': lambda src: __import__('polars').read_parquet(src),
    'pandas': lambda src: __import__('pandas').read_parquet(src),
    'pyarrow': lambda src: __import__(
        'pyarrow.parquet',
    ).parquet.read_table(src),
}


def _detect_backend() -> str:
    """Detect the first available DataFrame backend.

    Tries polars, pandas, pyarrow in order.

    Returns:
        The name of the first available backend.

    Raises:
        BackendNotAvailableError:
            If none of the backends is installed.
    """

    for name in _BACKEND_ORDER:
        try:
            __import__(name)
            logger.debug('Auto-detected backend: %s', name)
            return name
        except ImportError:
            logger.debug('Backend %s not available', name)

    msg = (
        'No DataFrame backend available; '
        'install at least one of: polars, pandas, pyarrow'
    )
    logger.error(msg)

    raise BackendNotAvailableError(msg)


def _read_parquet(
    source: str | Path | io.BytesIO,
    backend: str,
) -> Any:
    """Read a Parquet file into the requested backend.

    Tries the requested backend first, then falls back through
    alternatives in order.

    Args:
        source:
            Path to a Parquet file or an in-memory buffer.
        backend:
            Target backend name.

    Returns:
        A DataFrame or Table in the available backend.
    """

    # Build the order: requested backend first, then the rest
    order = [backend] + [b for b in _BACKEND_ORDER if b != backend]

    for name in order:
        reader = _PARQUET_READERS.get(name)

        if reader is None:
            continue

        try:
            result = reader(source)
        except ImportError:
            if name == backend:
                logger.warning(
                    '%s requested but not installed; '
                    'trying alternative backends',
                    name,
                )
            else:
                logger.debug('Fallback %s not available', name)

            continue

        if name != backend:
            logger.warning(
                'Using %s as fallback (requested %s)',
                name,
                backend,
            )

        logger.debug('Reading Parquet with %s', name)
        return result

    msg = 'Cannot read Parquet: none of polars, pandas, or pyarrow is installed'
    logger.error(msg)

    raise BackendNotAvailableError(msg)


def parse_response(
    source: str | Path | io.BytesIO,
    response_format: ResponseFormat = 'parquet',
    backend: BackendType = 'auto',
) -> Any:
    """Parse an API response and convert to the requested backend.

    Args:
        source:
            Path to a file or an in-memory buffer.
        response_format:
            The format of the response data.
        backend:
            The target DataFrame backend. Use ``'auto'`` to select
            the first available backend (tries polars, pandas,
            pyarrow in order).

    Returns:
        A DataFrame in the requested backend format.
    """

    if response_format == 'parquet':
        target = _detect_backend() if backend == 'auto' else backend
        logger.info(
            'Parsing %s response with backend=%s',
            response_format,
            target,
        )
        return _read_parquet(source, target)

    if response_format == 'json':
        import json

        logger.info('Parsing JSON response')

        if isinstance(source, (str, Path)):
            with open(source) as f:
                return json.load(f)

        return json.loads(source.read())

    raise ValueError(f'Unsupported response format: {response_format!r}')
