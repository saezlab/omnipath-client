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
    identify,
    map_name,
    map_name0,
    map_names,
    translate,
    all_mappings,
    translation_df,
    translate_column,
    translation_dict,
    translate_columns,
)
from omnipath_client.utils._reflists import (
    get_reflist,
    is_swissprot,
    all_swissprots,
)
from omnipath_client.utils._taxonomy import (
    organisms_df,
    all_organisms,
    resolve_organism,
    ensure_latin_name,
    ensure_common_name,
    ensure_ncbi_tax_id,
)
from omnipath_client.utils._orthology import (
    translate as orthology_translate,
    orthology_df,
    orthology_dict,
    translate_column as orthology_translate_column,
)
