"""COSMOS PKN fetch and convenience functions."""

from __future__ import annotations

import logging
from typing import Any

from omnipath_client._download import Downloader
from omnipath_client._session import get_logger

logger = get_logger(__name__)

DEFAULT_METABO_URL = 'https://metabo.omnipathdb.org'

_metabo_url: str = DEFAULT_METABO_URL
_downloader: Downloader | None = None


def set_url(url: str) -> None:
    """Override the metabo service base URL."""

    global _metabo_url
    _metabo_url = url


def _dl() -> Downloader:
    """Lazy-initialised shared downloader."""

    global _downloader

    if _downloader is None:
        _downloader = Downloader(use_cache=False)

    return _downloader


def _resolve_organism(organism: int | str) -> int:
    """Resolve organism to NCBI taxonomy ID via the utils service."""

    if isinstance(organism, int):
        return organism

    # Try parsing as int first (e.g. '9606')
    try:
        return int(organism)
    except (ValueError, TypeError):
        pass

    from omnipath_client.utils import ensure_ncbi_tax_id

    result = ensure_ncbi_tax_id(organism)

    if result is None:
        raise ValueError(f'Could not resolve organism: {organism!r}')

    return result


def get_pkn(
    organism: int | str = 9606,
    categories: str | list[str] = 'all',
    resources: str | list[str] | None = None,
    format: str = 'dataframe',
) -> Any:
    """Fetch COSMOS PKN from the metabo service.

    Args:
        organism:
            Organism identifier — any form accepted by omnipath-utils
            taxonomy: NCBI ID (``9606``), common name (``'human'``),
            Latin (``'Homo sapiens'``), Ensembl (``'hsapiens'``),
            KEGG (``'hsa'``), etc.
        categories:
            Category names or ``'all'``.  Available categories:
            ``transporters``, ``receptors``, ``allosteric``,
            ``enzyme_metabolite``, ``ppi``, ``grn``.
        resources:
            Optional resource filter (comma-separated string or list).
        format:
            Output format: ``'dataframe'`` (default), ``'parquet'``,
            ``'dict'``, or ``'annnet'``.

    Returns:
        DataFrame (polars/pandas), raw dict, bytes (parquet), or
        AnnNet Graph depending on *format*.

    Example::

        import omnipath_client as oc

        # All human transporters
        df = oc.cosmos.get_pkn('human', categories='transporters')

        # Full mouse PKN as AnnNet graph
        g = oc.cosmos.get_pkn('mouse', format='annnet')
    """

    ncbi_tax_id = _resolve_organism(organism)

    if isinstance(categories, list):
        categories = ','.join(categories)

    if isinstance(resources, list):
        resources = ','.join(resources)

    params: dict[str, Any] = {
        'organism': ncbi_tax_id,
        'categories': categories,
    }

    if resources:
        params['resources'] = resources

    if format == 'parquet':
        params['format'] = 'parquet'

    url = f'{_metabo_url}/cosmos/pkn'
    data = _dl().fetch_json(url, params=params)

    if format == 'dict':
        return data

    if format == 'annnet':
        df = _network_to_dataframe(data['network'])
        from omnipath_client.cosmos._annnet import to_annnet
        return to_annnet(df)

    # Default: DataFrame
    return _network_to_dataframe(data['network'])


def _network_to_dataframe(records: list[dict]) -> Any:
    """Convert network records to a DataFrame.

    Uses polars if available, falls back to pandas.
    """

    if not records:
        try:
            import polars as pl
            return pl.DataFrame()
        except ImportError:
            import pandas as pd
            return pd.DataFrame()

    try:
        import polars as pl
        return pl.DataFrame(records)
    except ImportError:
        pass

    try:
        import pandas as pd
        return pd.DataFrame(records)
    except ImportError:
        pass

    raise ImportError(
        'Either polars or pandas is required for DataFrame output. '
        'Install with: pip install polars'
    )


def categories() -> list[str]:
    """List available PKN categories."""

    url = f'{_metabo_url}/cosmos/categories'
    return _dl().fetch_json(url)


def organisms() -> list[int]:
    """List organisms with pre-built PKNs."""

    url = f'{_metabo_url}/cosmos/organisms'
    return _dl().fetch_json(url)


def resources(organism: int | str = 9606) -> dict[str, list[str]]:
    """List resources available per category.

    Args:
        organism: Organism identifier (any form).
    """

    ncbi_tax_id = _resolve_organism(organism)
    url = f'{_metabo_url}/cosmos/resources'
    return _dl().fetch_json(url, params={'organism': ncbi_tax_id})


def status() -> dict:
    """Get cache status from the metabo service."""

    url = f'{_metabo_url}/cosmos/status'
    return _dl().fetch_json(url)
