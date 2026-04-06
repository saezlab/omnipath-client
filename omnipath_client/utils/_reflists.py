"""Reference lists client."""

from __future__ import annotations

from omnipath_client.utils._base import _get


def get_reflist(list_name: str, ncbi_tax_id: int = 9606) -> set[str]:
    """Get a reference list."""

    data = _get(f'/reflists/{list_name}', {'ncbi_tax_id': ncbi_tax_id})

    return set(data.get('identifiers', []))


def all_swissprots(ncbi_tax_id: int = 9606) -> set[str]:
    """Get all Swiss-Prot accessions for an organism."""

    return get_reflist('swissprot', ncbi_tax_id)


def all_trembls(ncbi_tax_id: int = 9606) -> set[str]:
    """Get all TrEMBL accessions for an organism."""

    return get_reflist('trembl', ncbi_tax_id)


def is_swissprot(uniprot_ac: str, ncbi_tax_id: int = 9606) -> bool:
    """Check if a UniProt accession is in Swiss-Prot."""

    return uniprot_ac in all_swissprots(ncbi_tax_id)
