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


class TestTaxonomy:

    @patch('omnipath_client.utils._taxonomy._get')
    def test_resolve(self, mock_get):
        mock_get.return_value = {
            'ncbi_tax_id': 9606,
            'common_name': 'human',
        }
        from omnipath_client.utils import ensure_ncbi_tax_id

        assert ensure_ncbi_tax_id('human') == 9606


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
            ['TP53'], source=9606, target=10090,
        )
        assert result['TP53'] == {'Trp53'}
