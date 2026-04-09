"""Tests for the utils client."""

from unittest.mock import patch

from omnipath_client.utils._base import (
    get_utils_url,
    set_utils_url,
)


class TestBase:

    def test_default_url(self):
        assert 'utils.omnipathdb.org' in get_utils_url()

    def test_set_url(self):
        old = get_utils_url()
        set_utils_url('http://localhost:8083')
        assert get_utils_url() == 'http://localhost:8083'
        set_utils_url(old)


class TestMapping:

    @patch('omnipath_client.utils._mapping._get')
    def test_map_name(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['P04637']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import map_name

        result = map_name('TP53', 'genesymbol', 'uniprot')
        assert result == {'P04637'}

    @patch('omnipath_client.utils._mapping._post')
    def test_translate_batch(self, mock_post):
        mock_post.return_value = {
            'results': {'TP53': ['P04637'], 'EGFR': ['P00533']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import translate

        # Use a list > 10 to trigger POST
        translate(
            ['A'] * 11,
            'genesymbol',
            'uniprot',
        )
        mock_post.assert_called_once()

    @patch('omnipath_client.utils._mapping._get')
    def test_id_types(self, mock_get):
        mock_get.return_value = [{'name': 'uniprot', 'label': 'UniProt'}]
        from omnipath_client.utils import id_types

        result = id_types()
        assert result[0]['name'] == 'uniprot'


class TestMappingExtra:

    @patch('omnipath_client.utils._mapping._get')
    def test_map_names(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['P04637'], 'EGFR': ['P00533']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import map_names

        result = map_names(['TP53', 'EGFR'], 'genesymbol', 'uniprot')
        assert 'P04637' in result
        assert 'P00533' in result

    @patch('omnipath_client.utils._mapping._get')
    def test_map_name0(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['P04637']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import map_name0

        assert map_name0('TP53', 'genesymbol', 'uniprot') == 'P04637'

    @patch('omnipath_client.utils._mapping._get')
    def test_map_name0_missing(self, mock_get):
        mock_get.return_value = {
            'results': {},
            'unmapped': ['FAKE'],
            'meta': {},
        }
        from omnipath_client.utils import map_name0

        assert map_name0('FAKE', 'genesymbol', 'uniprot') is None

    @patch('omnipath_client.utils._mapping._get')
    def test_map_name_with_raw(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['P04637']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import map_name

        map_name('TP53', 'genesymbol', 'uniprot', raw=True)
        # Verify raw=True was passed in params
        call_params = mock_get.call_args[0][1]  # second positional arg is params
        assert call_params.get('raw') is True

    @patch('omnipath_client.utils._mapping._get')
    def test_map_name_with_backend(self, mock_get):
        mock_get.return_value = {
            'results': {},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import map_name

        map_name('TP53', 'genesymbol', 'uniprot', backend='biomart')
        call_params = mock_get.call_args[0][1]
        assert call_params.get('backend') == 'biomart'

    @patch('omnipath_client.utils._mapping._get')
    def test_translate_small_uses_get(self, mock_get):
        mock_get.return_value = {
            'results': {'A': ['B']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils._mapping import translate

        translate(['A', 'B', 'C'], 'genesymbol', 'uniprot')
        mock_get.assert_called_once()  # <=10 IDs -> GET


class TestTaxonomy:

    @patch('omnipath_client.utils._taxonomy._get')
    def test_resolve(self, mock_get):
        mock_get.return_value = {
            'ncbi_tax_id': 9606,
            'common_name': 'human',
        }
        from omnipath_client.utils import ensure_ncbi_tax_id

        assert ensure_ncbi_tax_id('human') == 9606


class TestTaxonomyExtra:

    @patch('omnipath_client.utils._taxonomy._get')
    def test_ensure_common_name(self, mock_get):
        mock_get.return_value = {
            'ncbi_tax_id': 9606,
            'common_name': 'human',
            'latin_name': 'Homo sapiens',
        }
        from omnipath_client.utils import ensure_common_name

        assert ensure_common_name(9606) == 'human'

    @patch('omnipath_client.utils._taxonomy._get')
    def test_ensure_latin_name(self, mock_get):
        mock_get.return_value = {
            'ncbi_tax_id': 9606,
            'latin_name': 'Homo sapiens',
        }
        from omnipath_client.utils import ensure_latin_name

        assert ensure_latin_name(9606) == 'Homo sapiens'

    @patch('omnipath_client.utils._taxonomy._get')
    def test_all_organisms(self, mock_get):
        mock_get.return_value = [{'ncbi_tax_id': 9606, 'common_name': 'human'}]
        from omnipath_client.utils import all_organisms

        result = all_organisms()
        assert len(result) == 1
        assert result[0]['ncbi_tax_id'] == 9606

    @patch('omnipath_client.utils._taxonomy._get')
    def test_ensure_unknown_returns_none(self, mock_get):
        mock_get.return_value = {'ncbi_tax_id': None}
        from omnipath_client.utils import ensure_ncbi_tax_id

        assert ensure_ncbi_tax_id('alien') is None


class TestOrthology:

    @patch('omnipath_client.utils._orthology._get')
    def test_translate(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['Trp53']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import orthology_translate

        result = orthology_translate(
            ['TP53'],
            source=9606,
            target=10090,
        )
        assert result['TP53'] == {'Trp53'}


class TestReflists:

    @patch('omnipath_client.utils._reflists._get')
    def test_get_reflist(self, mock_get):
        mock_get.return_value = {
            'identifiers': ['P04637', 'P00533'],
            'count': 2,
        }
        from omnipath_client.utils import get_reflist

        result = get_reflist('swissprot')
        assert result == {'P04637', 'P00533'}

    @patch('omnipath_client.utils._reflists._get')
    def test_all_swissprots(self, mock_get):
        mock_get.return_value = {
            'identifiers': ['P04637'],
            'count': 1,
        }
        from omnipath_client.utils import all_swissprots

        assert 'P04637' in all_swissprots()

    @patch('omnipath_client.utils._reflists._get')
    def test_is_swissprot(self, mock_get):
        mock_get.return_value = {
            'identifiers': ['P04637'],
            'count': 1,
        }
        from omnipath_client.utils import is_swissprot

        assert is_swissprot('P04637')
        assert not is_swissprot('FAKE')


class TestOrthologyExtra:

    @patch('omnipath_client.utils._orthology._get')
    def test_translate_with_resource(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['Trp53']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import orthology_translate

        orthology_translate(
            ['TP53'],
            source=9606,
            target=10090,
            resource='hcop',
        )
        call_params = mock_get.call_args[0][1]
        assert call_params.get('resource') == 'hcop'

    @patch('omnipath_client.utils._orthology._get')
    def test_translate_with_min_sources(self, mock_get):
        mock_get.return_value = {
            'results': {'TP53': ['Trp53']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import orthology_translate

        orthology_translate(
            ['TP53'],
            source=9606,
            target=10090,
            min_sources=3,
        )
        call_params = mock_get.call_args[0][1]
        assert call_params.get('min_sources') == 3



class TestIdentify:

    @patch('omnipath_client.utils._mapping._get')
    def test_identify(self, mock_get):
        mock_get.return_value = {
            'results': {
                'P04637': [
                    {'id_type': 'uniprot', 'role': 'source', 'mappings_count': 5},
                ],
            },
            'meta': {'ncbi_tax_id': 9606, 'total_input': 1},
        }
        from omnipath_client.utils import identify

        result = identify(['P04637'])
        assert 'P04637' in result
        assert result['P04637'][0]['id_type'] == 'uniprot'

    @patch('omnipath_client.utils._mapping._get')
    def test_identify_params(self, mock_get):
        mock_get.return_value = {'results': {}, 'meta': {}}
        from omnipath_client.utils import identify

        identify(['P04637', 'HMDB0000001'], ncbi_tax_id=10090)
        call_params = mock_get.call_args[0][1]
        assert call_params['identifiers'] == 'P04637,HMDB0000001'
        assert call_params['ncbi_tax_id'] == 10090


class TestAllMappings:

    @patch('omnipath_client.utils._mapping._get')
    def test_all_mappings(self, mock_get):
        mock_get.return_value = {
            'results': {
                'P04637': {'genesymbol': ['TP53'], 'entrez': ['7157']},
            },
            'meta': {},
        }
        from omnipath_client.utils import all_mappings

        result = all_mappings(['P04637'], 'uniprot')
        assert 'P04637' in result
        assert 'genesymbol' in result['P04637']
        assert result['P04637']['genesymbol'] == ['TP53']

    @patch('omnipath_client.utils._mapping._get')
    def test_all_mappings_params(self, mock_get):
        mock_get.return_value = {'results': {}, 'meta': {}}
        from omnipath_client.utils import all_mappings

        all_mappings(['P04637'], 'uniprot', ncbi_tax_id=10090)
        call_params = mock_get.call_args[0][1]
        assert call_params['identifiers'] == 'P04637'
        assert call_params['id_type'] == 'uniprot'
        assert call_params['ncbi_tax_id'] == 10090


class TestDownloadImportFix:
    """Verify the dlmachine import fix."""

    def test_downloader_import(self):
        """_download.py should import from dlmachine, not download_manager."""
        import inspect

        from omnipath_client import _download

        source = inspect.getsource(_download)
        assert 'from dlmachine import' in source
        assert 'from download_manager import' not in source


class TestIntrospection:
    """Test endpoint introspection functions."""

    def test_endpoints_importable(self):
        from omnipath_client import endpoints
        assert callable(endpoints)

    def test_params_importable(self):
        from omnipath_client import params
        assert callable(params)

    def test_values_importable(self):
        from omnipath_client import values
        assert callable(values)


class TestTranslationData:

    @patch('omnipath_client.utils._mapping._get')
    def test_translation_dict_full_table(self, mock_get):
        """Full table (no identifiers)."""
        mock_get.return_value = {
            'table': {'TP53': ['P04637'], 'EGFR': ['P00533']},
            'meta': {},
        }
        from omnipath_client.utils import translation_dict

        result = translation_dict('genesymbol', 'uniprot')
        assert result == {'TP53': {'P04637'}, 'EGFR': {'P00533'}}

    @patch('omnipath_client.utils._mapping._get')
    def test_translation_dict_with_ids(self, mock_get):
        """Specific IDs."""
        mock_get.return_value = {
            'results': {'TP53': ['P04637']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import translation_dict

        result = translation_dict(
            'genesymbol', 'uniprot', identifiers=['TP53'],
        )
        assert result == {'TP53': {'P04637'}}

    @patch('omnipath_client.utils._mapping._get')
    def test_translation_df_full(self, mock_get):
        mock_get.return_value = {
            'table': {'TP53': ['P04637']},
            'meta': {},
        }
        from omnipath_client.utils import translation_df

        result = translation_df('genesymbol', 'uniprot')
        assert hasattr(result, 'columns') or hasattr(result, 'schema')


class TestOrthologyData:

    @patch('omnipath_client.utils._orthology._get')
    def test_orthology_dict_full_table(self, mock_get):
        """Full table (no identifiers)."""
        mock_get.return_value = {
            'table': {'TP53': ['Trp53'], 'EGFR': ['Egfr']},
            'meta': {},
        }
        from omnipath_client.utils import orthology_dict

        result = orthology_dict(source=9606, target=10090)
        assert result == {'TP53': {'Trp53'}, 'EGFR': {'Egfr'}}

    @patch('omnipath_client.utils._orthology._get')
    def test_orthology_dict_with_ids(self, mock_get):
        """Specific IDs."""
        mock_get.return_value = {
            'results': {'TP53': ['Trp53']},
            'unmapped': [],
            'meta': {},
        }
        from omnipath_client.utils import orthology_dict

        result = orthology_dict(
            source=9606, target=10090, identifiers=['TP53'],
        )
        assert result == {'TP53': {'Trp53'}}

    @patch('omnipath_client.utils._orthology._get')
    def test_orthology_df_full(self, mock_get):
        mock_get.return_value = {
            'table': {'TP53': ['Trp53']},
            'meta': {},
        }
        from omnipath_client.utils import orthology_df

        result = orthology_df(source=9606, target=10090)
        assert hasattr(result, 'columns') or hasattr(result, 'schema')


class TestTaxonomyDf:

    @patch('omnipath_client.utils._taxonomy._get')
    def test_organisms_df(self, mock_get):
        mock_get.return_value = [{'ncbi_tax_id': 9606, 'common_name': 'human'}]
        from omnipath_client.utils import organisms_df

        result = organisms_df()
        assert hasattr(result, 'columns') or hasattr(result, 'schema')

    @patch('omnipath_client.utils._taxonomy._get')
    def test_organisms_df_mixed_types(self, mock_get):
        """Organisms with None and string values for optional fields."""
        mock_get.return_value = [
            {'ncbi_tax_id': 9606, 'common_name': 'human', 'kegg_code': 'hsa'},
            {'ncbi_tax_id': 10090, 'common_name': 'mouse', 'kegg_code': None},
        ]
        from omnipath_client.utils import organisms_df

        result = organisms_df()
        assert hasattr(result, 'columns') or hasattr(result, 'schema')
