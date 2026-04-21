"""Tests for the COSMOS PKN client module."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


# -- Sample data used across tests ------------------------------------------

SAMPLE_NETWORK = [
    {
        'source': 'TP53',
        'target': 'MDM2',
        'source_type': 'protein',
        'target_type': 'protein',
        'interaction_type': 'ppi',
        'resource': 'Signor',
        'mor': 1,
    },
    {
        'source': 'ATP',
        'target': 'EGFR',
        'source_type': 'small_molecule',
        'target_type': 'protein',
        'interaction_type': 'enzyme_metabolite',
        'resource': 'BRENDA',
        'mor': -1,
    },
    {
        'source': 'TP53',
        'target': 'BCL2',
        'source_type': 'protein',
        'target_type': 'protein',
        'interaction_type': 'grn',
        'resource': 'DoRothEA',
        'mor': 0,
    },
]

SAMPLE_PKN_RESPONSE = {'network': SAMPLE_NETWORK}


# -- Helpers -----------------------------------------------------------------

def _make_annnet_mock():
    """Build a fake ``annnet.core.graph`` module with a mock AnnNet class.

    Returns ``(mock_annnet_graph_module, mock_graph_instance)``.
    """

    mock_graph = MagicMock()
    MockAnnNet = MagicMock(return_value=mock_graph)

    annnet_mod = ModuleType('annnet')
    core_mod = ModuleType('annnet.core')
    graph_mod = ModuleType('annnet.core.graph')
    graph_mod.AnnNet = MockAnnNet  # type: ignore[attr-defined]
    annnet_mod.core = core_mod  # type: ignore[attr-defined]
    core_mod.graph = graph_mod  # type: ignore[attr-defined]

    return {
        'annnet': annnet_mod,
        'annnet.core': core_mod,
        'annnet.core.graph': graph_mod,
    }, mock_graph


def _make_df(records):
    """Create a DataFrame from records using whatever library is available.

    Returns ``(df, library_name)``.
    """

    try:
        import polars as pl
        return pl.DataFrame(records), 'polars'
    except ImportError:
        pass

    try:
        import pandas as pd
        return pd.DataFrame(records), 'pandas'
    except ImportError:
        pass

    pytest.skip('Neither polars nor pandas is installed')


# -- Fixtures ---------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_downloader():
    """Reset the module-level downloader singleton between tests."""

    import omnipath_client.cosmos._pkn as pkn_mod

    old_dl = pkn_mod._downloader
    pkn_mod._downloader = None
    yield
    pkn_mod._downloader = old_dl


@pytest.fixture
def mock_dl():
    """Patch Downloader in _pkn and return the mock instance."""

    with patch('omnipath_client.cosmos._pkn.Downloader') as MockCls:
        inst = MagicMock()
        MockCls.return_value = inst
        yield inst


@pytest.fixture
def annnet_modules():
    """Inject fake annnet modules into sys.modules for the duration of a test."""

    modules, mock_graph = _make_annnet_mock()
    originals = {k: sys.modules.get(k) for k in modules}

    sys.modules.update(modules)
    yield mock_graph

    for key, orig in originals.items():
        if orig is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = orig


# -- get_pkn tests: format='dict' -------------------------------------------

class TestGetPknFormatDict:
    """get_pkn with format='dict' returns the raw JSON dict."""

    def test_returns_raw_dict(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        result = get_pkn(organism=9606, format='dict')

        assert result is SAMPLE_PKN_RESPONSE
        mock_dl.fetch_json.assert_called_once()

    def test_default_categories_all(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['categories'] == 'all'
        assert params['organism'] == 9606

    def test_specific_categories_list(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(categories=['transporters', 'receptors'], format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['categories'] == 'transporters,receptors'

    def test_specific_categories_string(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(categories='transporters', format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['categories'] == 'transporters'

    def test_resource_filtering_string(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(resources='Signor', format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['resources'] == 'Signor'

    def test_resource_filtering_list(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(resources=['Signor', 'BRENDA'], format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['resources'] == 'Signor,BRENDA'

    def test_no_resources_key_when_none(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(resources=None, format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert 'resources' not in params

    def test_url_uses_metabo_base(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(format='dict')

        url = mock_dl.fetch_json.call_args[0][0]
        assert url.endswith('/cosmos/pkn')
        assert 'metabo.omnipathdb.org' in url


# -- get_pkn tests: format='dataframe' --------------------------------------

class TestGetPknFormatDataframe:
    """get_pkn with format='dataframe' returns a DataFrame."""

    def test_returns_dataframe(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        df = get_pkn(format='dataframe')

        assert hasattr(df, 'columns')
        assert 'source' in df.columns
        assert 'target' in df.columns
        assert 'source_type' in df.columns
        assert len(df) == 3

    def test_default_format_is_dataframe(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        df = get_pkn()

        assert hasattr(df, 'columns')
        assert len(df) == 3

    def test_empty_network_returns_empty_df(self, mock_dl):
        mock_dl.fetch_json.return_value = {'network': []}

        from omnipath_client.cosmos import get_pkn

        df = get_pkn(format='dataframe')

        assert len(df) == 0


# Skip entire DataFrame class when neither library is available
_has_df_lib = False
try:
    import polars
    _has_df_lib = True
except ImportError:
    try:
        import pandas
        _has_df_lib = True
    except ImportError:
        pass

if not _has_df_lib:
    TestGetPknFormatDataframe = pytest.mark.skip(  # type: ignore[misc]
        reason='Neither polars nor pandas is installed',
    )(TestGetPknFormatDataframe)


# -- get_pkn tests: format='annnet' -----------------------------------------

class TestGetPknFormatAnnnet:
    """get_pkn with format='annnet' converts to AnnNet Graph."""

    @pytest.mark.skipif(not _has_df_lib, reason='DataFrame library required')
    def test_calls_to_annnet(self, mock_dl, annnet_modules):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE
        mock_graph = annnet_modules

        from omnipath_client.cosmos import get_pkn

        result = get_pkn(format='annnet')

        assert result is mock_graph
        mock_graph.add_vertices_bulk.assert_called_once()
        mock_graph.add_edges_bulk.assert_called_once()


# -- get_pkn tests: organism resolution --------------------------------------

class TestGetPknOrganismResolution:
    """Organism normalisation in get_pkn."""

    def test_int_organism_passed_directly(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(organism=10090, format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['organism'] == 10090

    def test_numeric_string_parsed_as_int(self, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(organism='9606', format='dict')

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['organism'] == 9606

    @patch('omnipath_client.cosmos._pkn._resolve_organism', return_value=9606)
    def test_string_organism_calls_resolve(self, mock_resolve, mock_dl):
        mock_dl.fetch_json.return_value = SAMPLE_PKN_RESPONSE

        from omnipath_client.cosmos import get_pkn

        get_pkn(organism='human', format='dict')

        mock_resolve.assert_called_once_with('human')

    def test_resolve_organism_calls_ensure_ncbi_tax_id(self):
        with patch(
            'omnipath_client.utils.ensure_ncbi_tax_id',
            return_value=10090,
        ) as mock_ensure:
            from omnipath_client.cosmos._pkn import _resolve_organism

            result = _resolve_organism('mouse')

        assert result == 10090
        mock_ensure.assert_called_once_with('mouse')

    def test_resolve_organism_raises_on_unknown(self):
        with patch(
            'omnipath_client.utils.ensure_ncbi_tax_id',
            return_value=None,
        ):
            from omnipath_client.cosmos._pkn import _resolve_organism

            with pytest.raises(ValueError, match='Could not resolve'):
                _resolve_organism('alien_species')


# -- to_annnet tests --------------------------------------------------------

class TestToAnnnet:
    """Tests for to_annnet() conversion."""

    def test_vertices_extracted_from_source_target(self, annnet_modules):
        mock_graph = annnet_modules
        df, _ = _make_df(SAMPLE_NETWORK)

        from omnipath_client.cosmos import to_annnet

        to_annnet(df)

        vertices = mock_graph.add_vertices_bulk.call_args[0][0]
        vertex_ids = {v['vertex_id'] for v in vertices}
        assert vertex_ids == {'TP53', 'MDM2', 'ATP', 'EGFR', 'BCL2'}

    def test_edges_added_in_bulk(self, annnet_modules):
        mock_graph = annnet_modules
        df, _ = _make_df(SAMPLE_NETWORK)

        from omnipath_client.cosmos import to_annnet

        to_annnet(df)

        edges = mock_graph.add_edges_bulk.call_args[0][0]
        assert len(edges) == 3
        assert edges[0]['source'] == 'TP53'
        assert edges[0]['target'] == 'MDM2'
        assert edges[0]['weight'] == 1.0
        assert edges[1]['weight'] == -1.0

    def test_entity_types_preserved(self, annnet_modules):
        mock_graph = annnet_modules
        df, _ = _make_df(SAMPLE_NETWORK)

        from omnipath_client.cosmos import to_annnet

        to_annnet(df)

        vertices = mock_graph.add_vertices_bulk.call_args[0][0]
        type_map = {v['vertex_id']: v['entity_type'] for v in vertices}
        assert type_map['TP53'] == 'protein'
        assert type_map['ATP'] == 'small_molecule'
        assert type_map['EGFR'] == 'protein'

    def test_edge_attributes(self, annnet_modules):
        mock_graph = annnet_modules
        df, _ = _make_df(SAMPLE_NETWORK)

        from omnipath_client.cosmos import to_annnet

        to_annnet(df)

        edges = mock_graph.add_edges_bulk.call_args[0][0]
        assert edges[0]['attributes']['interaction_type'] == 'ppi'
        assert edges[0]['attributes']['resource'] == 'Signor'
        assert edges[0]['edge_directed'] is True

    def test_works_with_pandas(self, annnet_modules):
        pd = pytest.importorskip('pandas')
        mock_graph = annnet_modules

        from omnipath_client.cosmos import to_annnet

        df = pd.DataFrame(SAMPLE_NETWORK)
        result = to_annnet(df)

        assert result is mock_graph
        mock_graph.add_vertices_bulk.assert_called_once()
        mock_graph.add_edges_bulk.assert_called_once()

    def test_works_with_polars(self, annnet_modules):
        pl = pytest.importorskip('polars')
        mock_graph = annnet_modules

        from omnipath_client.cosmos import to_annnet

        df = pl.DataFrame(SAMPLE_NETWORK)
        result = to_annnet(df)

        assert result is mock_graph
        mock_graph.add_vertices_bulk.assert_called_once()
        mock_graph.add_edges_bulk.assert_called_once()

        vertices = mock_graph.add_vertices_bulk.call_args[0][0]
        edges = mock_graph.add_edges_bulk.call_args[0][0]
        assert len(vertices) == 5
        assert len(edges) == 3

    def test_raises_import_error_without_annnet(self):
        df, _ = _make_df(SAMPLE_NETWORK)

        # Remove annnet from sys.modules so the real import fails
        saved = {}
        for key in list(sys.modules):
            if key == 'annnet' or key.startswith('annnet.'):
                saved[key] = sys.modules.pop(key)

        try:
            from omnipath_client.cosmos._annnet import to_annnet

            with pytest.raises(ImportError, match='annnet is required'):
                to_annnet(df)
        finally:
            sys.modules.update(saved)


# -- Convenience function tests ----------------------------------------------

class TestCategories:

    def test_returns_list(self, mock_dl):
        mock_dl.fetch_json.return_value = [
            'transporters',
            'receptors',
            'allosteric',
            'enzyme_metabolite',
            'ppi',
            'grn',
        ]

        from omnipath_client.cosmos import categories

        result = categories()

        assert isinstance(result, list)
        assert 'transporters' in result
        assert 'grn' in result
        assert len(result) == 6

    def test_calls_correct_url(self, mock_dl):
        mock_dl.fetch_json.return_value = []

        from omnipath_client.cosmos._pkn import categories

        categories()

        url = mock_dl.fetch_json.call_args[0][0]
        assert url.endswith('/cosmos/categories')


class TestOrganisms:

    def test_returns_list_of_ints(self, mock_dl):
        mock_dl.fetch_json.return_value = [9606, 10090, 10116]

        from omnipath_client.cosmos import organisms

        result = organisms()

        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
        assert 9606 in result
        assert len(result) == 3

    def test_calls_correct_url(self, mock_dl):
        mock_dl.fetch_json.return_value = []

        from omnipath_client.cosmos._pkn import organisms

        organisms()

        url = mock_dl.fetch_json.call_args[0][0]
        assert url.endswith('/cosmos/organisms')


class TestResources:

    def test_returns_dict(self, mock_dl):
        mock_dl.fetch_json.return_value = {
            'transporters': ['ABC_family', 'SLC_family'],
            'receptors': ['CellPhoneDB'],
        }

        from omnipath_client.cosmos import resources

        result = resources()

        assert isinstance(result, dict)
        assert 'transporters' in result
        assert isinstance(result['transporters'], list)

    def test_passes_organism_param(self, mock_dl):
        mock_dl.fetch_json.return_value = {}

        from omnipath_client.cosmos import resources

        resources(organism=10090)

        params = mock_dl.fetch_json.call_args.kwargs['params']
        assert params['organism'] == 10090

    @patch('omnipath_client.cosmos._pkn._resolve_organism', return_value=10090)
    def test_resolves_string_organism(self, mock_resolve, mock_dl):
        mock_dl.fetch_json.return_value = {}

        from omnipath_client.cosmos import resources

        resources(organism='mouse')

        mock_resolve.assert_called_once_with('mouse')


class TestStatus:

    def test_returns_dict(self, mock_dl):
        mock_dl.fetch_json.return_value = {
            'organisms': {
                '9606': {'status': 'ready', 'last_built': '2026-01-15'},
            },
            'version': '0.2.0',
        }

        from omnipath_client.cosmos import status

        result = status()

        assert isinstance(result, dict)
        assert 'organisms' in result
        assert 'version' in result

    def test_calls_correct_url(self, mock_dl):
        mock_dl.fetch_json.return_value = {}

        from omnipath_client.cosmos._pkn import status

        status()

        url = mock_dl.fetch_json.call_args[0][0]
        assert url.endswith('/cosmos/status')


# -- set_url tests -----------------------------------------------------------

class TestSetUrl:

    def test_set_and_reset(self):
        import omnipath_client.cosmos._pkn as pkn_mod

        old = pkn_mod._metabo_url
        pkn_mod.set_url('http://localhost:9999')
        assert pkn_mod._metabo_url == 'http://localhost:9999'
        pkn_mod.set_url(old)
        assert pkn_mod._metabo_url == old
