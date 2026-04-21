"""COSMOS PKN client for the OmniPath Metabolomics service.

Fetches pre-built COSMOS prior-knowledge networks from
``metabo.omnipathdb.org`` as DataFrames or AnnNet Graph objects.

Example::

    import omnipath_client as oc

    # DataFrame (polars by default)
    df = oc.cosmos.get_pkn(organism='human', categories='transporters')

    # AnnNet Graph
    g = oc.cosmos.get_pkn(organism='human', format='annnet')

    # Available categories and organisms
    oc.cosmos.categories()   # ['transporters', 'receptors', ...]
    oc.cosmos.organisms()    # [9606, 10090, 10116]
"""

from omnipath_client.cosmos._pkn import (
    categories,
    get_pkn,
    organisms,
    resources,
    status,
)
from omnipath_client.cosmos._annnet import to_annnet

__all__ = [
    'categories',
    'get_pkn',
    'organisms',
    'resources',
    'status',
    'to_annnet',
]
