"""Taxonomy client."""

from __future__ import annotations

from omnipath_client.utils._base import _get


def resolve_organism(query: str | int) -> dict:
    """Resolve organism to all name forms."""

    return _get('/taxonomy/resolve', {'organism': str(query)})


def ensure_ncbi_tax_id(taxon: str | int) -> int | None:
    """Convert any organism identifier to NCBI Taxonomy ID."""

    data = resolve_organism(taxon)

    return data.get('ncbi_tax_id')


def ensure_common_name(taxon: str | int) -> str | None:
    """Convert any organism identifier to common name."""

    data = resolve_organism(taxon)

    return data.get('common_name')


def ensure_latin_name(taxon: str | int) -> str | None:
    """Convert any organism identifier to Latin name."""

    data = resolve_organism(taxon)

    return data.get('latin_name')


def all_organisms() -> list[dict]:
    """List all known organisms."""

    return _get('/taxonomy/organisms')
