"""Client for the OmniPath Utils web service.

Provides the same API as omnipath_utils.mapping,
omnipath_utils.taxonomy, etc., but fetches data from the
HTTP service instead of local backends.

Example::

    from omnipath_client.utils import map_name, translate_column

    map_name('TP53', 'genesymbol', 'uniprot')
    # {'P04637'}
"""

from omnipath_client.utils._mapping import (
    id_types,
    map_name,
    map_name0,
    map_names,
    translate,
    translate_column,
    translate_columns,
)
from omnipath_client.utils._reflists import (
    get_reflist,
    is_swissprot,
    all_swissprots,
)
from omnipath_client.utils._taxonomy import (
    all_organisms,
    resolve_organism,
    ensure_latin_name,
    ensure_common_name,
    ensure_ncbi_tax_id,
)
from omnipath_client.utils._orthology import (
    translate as orthology_translate,
    translate_column as orthology_translate_column,
)
