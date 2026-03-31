"""Type aliases and enums for omnipath-client."""

from __future__ import annotations

from typing import Literal


BackendType = Literal['polars', 'pandas', 'pyarrow']

ResponseFormat = Literal['parquet', 'json']
