"""Response parsing and DataFrame backend conversion."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from omnipath_client._errors import BackendNotAvailableError
from omnipath_client._session import get_logger
from omnipath_client._types import BackendType, ResponseFormat


logger = get_logger(__name__)


def _read_parquet(source: str | Path | io.BytesIO) -> Any:
    """Read a Parquet file into a pyarrow Table."""

    import pyarrow.parquet as pq

    logger.debug('Reading parquet response from %s', type(source).__name__)
    return pq.read_table(source)


def _to_backend(table: Any, backend: BackendType) -> Any:
    """Convert a pyarrow Table to the requested backend."""

    logger.debug('Converting response table to backend=%s', backend)

    if backend == 'pyarrow':
        return table

    if backend == 'polars':
        try:
            import polars as pl
        except ImportError as e:
            raise BackendNotAvailableError(
                'polars is not installed. Install it with: pip install polars',
            ) from e

        return pl.from_arrow(table)

    if backend == 'pandas':
        try:
            import pandas  # noqa: F401
        except ImportError as e:
            raise BackendNotAvailableError(
                'pandas is not installed. Install it with: pip install pandas',
            ) from e

        return table.to_pandas()

    raise ValueError(f'Unknown backend: {backend!r}')


def parse_response(
    source: str | Path | io.BytesIO,
    response_format: ResponseFormat = 'parquet',
    backend: BackendType = 'polars',
) -> Any:
    """Parse an API response and convert to the requested backend.

    Args:
        source:
            Path to a file or an in-memory buffer.
        response_format:
            The format of the response data.
        backend:
            The target DataFrame backend.

    Returns:
        A DataFrame in the requested backend format.
    """

    if response_format == 'parquet':
        logger.info(
            'Parsing %s response into backend=%s',
            response_format,
            backend,
        )
        table = _read_parquet(source)
        return _to_backend(table, backend)

    if response_format == 'json':
        import json

        logger.info('Parsing JSON response')

        if isinstance(source, (str, Path)):
            with open(source) as f:
                return json.load(f)

        return json.loads(source.read())

    raise ValueError(f'Unsupported response format: {response_format!r}')
