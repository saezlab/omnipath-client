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


class TestDownloadImportFix:
    """Verify the dlmachine import fix."""

    def test_downloader_import(self):
        """_download.py should import from dlmachine, not download_manager."""
        import inspect

        from omnipath_client import _download

        source = inspect.getsource(_download)
        assert 'from dlmachine import' in source
        assert 'from download_manager import' not in source
