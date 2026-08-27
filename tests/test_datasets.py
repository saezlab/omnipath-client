"""
Tests for the dataset accessors.

The registry is the service's, so these mock the one call that reads it
and assert what the accessors do with the answer -- above all that no
dataset name is written down in the client.
"""

import pytest

from omnipath_client import datasets
from omnipath_client._errors import OmniPathError


LIANA = {
    'value': 'liana',
    'count': 44457,
    'kind': 'ligand_receptor',
    'included_sources': ['connectomedb2025'],
    'interaction_class_scope': ['ligand_receptor'],
    'default_attributes': ['endpoints', 'label'],
    'mandatory_attributes': [],
}

METALINKSDB = {
    'value': 'metalinksdb',
    'count': 4491958,
    'kind': 'compound_protein',
    'included_sources': ['chembl', 'stitch'],
    'interaction_class_scope': [],
    'default_attributes': ['endpoints', 'label'],
    'mandatory_attributes': ['intercell'],
}

SURFACE = {
    'parameters': {
        'datasets': {'values': [METALINKSDB, LIANA]},
    },
}


@pytest.fixture
def registry(monkeypatch):
    """
    The parameter surface, without a service to read it from.
    """

    monkeypatch.setattr(
        datasets,
        'interaction_parameters',
        lambda **scope: SURFACE,
    )


class TestRegistry:
    """
    What the client knows about datasets, and where it learned it.
    """

    def test_names_come_from_the_service(self, registry):

        assert datasets.names() == ['metalinksdb', 'liana']

    def test_no_dataset_name_is_written_down_in_the_client(self):
        """
        The names are the build's, not the client's. A client carrying
        them would keep answering for a dataset a build had dropped, and
        would not reach one a build had added.
        """

        source = (datasets.__file__,)

        for path in source:
            with open(path) as fp:
                body = fp.read().split('"""', 2)[-1]

            assert 'metalinksdb' not in body

    def test_a_dataset_is_an_attribute(self, registry):

        assert datasets.liana.name == 'liana'
        assert repr(datasets.liana) == '<Dataset liana>'

    def test_completion_offers_the_registered_names(self, registry):

        offered = dir(datasets)

        assert 'liana' in offered
        assert 'metalinksdb' in offered

    def test_an_unregistered_name_says_what_is_registered(self, registry):

        with pytest.raises(AttributeError, match = 'metalinksdb'):
            datasets.nosuch

    def test_a_private_name_is_not_a_dataset(self, registry):
        """
        Import machinery asks for dunder attributes; answering them with
        a dataset would make every such probe a request to the service.
        """

        with pytest.raises(AttributeError):
            datasets.__wrapped__


class TestDataset:
    """
    The three questions asked of one dataset.
    """

    def test_info_is_the_registry_row(self, registry):

        assert datasets.liana.info() == LIANA

    def test_info_on_an_unknown_name_is_refused(self, registry):

        with pytest.raises(OmniPathError, match = 'nosuch'):
            datasets.info('nosuch')

    def test_resources_are_the_contributing_sources(self, registry):

        assert datasets.metalinksdb.resources() == ['chembl', 'stitch']

    def test_attributes_include_the_mandatory_ones(self, registry):
        """
        A dataset that always carries a layer projects it whether or not
        it is in the default list, so reporting only the defaults would
        understate what comes back.
        """

        assert datasets.metalinksdb.attributes() == [
            'endpoints',
            'label',
            'intercell',
        ]

    def test_stats_scope_to_the_one_dataset(self, registry, monkeypatch):

        seen = {}
        monkeypatch.setattr(
            datasets,
            'interaction_stats',
            lambda **scope: seen.update(scope) or {'total': 1},
        )

        assert datasets.liana.stats(organism='9606') == {'total': 1}
        assert seen == {'datasets': 'liana', 'organism': '9606'}

    def test_get_returns_a_frame_of_the_rows(self, registry, monkeypatch):

        page = {
            'interactions': [
                {'source': 'a', 'target': 'b'},
                {'source': 'c', 'target': 'd'},
            ],
            'total': 2,
        }
        monkeypatch.setattr(
            datasets,
            'interaction_dataset',
            lambda dataset, **params: page,
        )

        frame = datasets.liana.get(backend='pandas', limit=2)

        assert list(frame.columns) == ['source', 'target']
        assert len(frame) == 2

    def test_a_page_with_no_rows_is_still_a_frame(
        self,
        registry,
        monkeypatch,
    ):
        """
        A query that matched nothing must not become a different type,
        or every caller has to branch before using the result.
        """

        monkeypatch.setattr(
            datasets,
            'interaction_dataset',
            lambda dataset, **params: {'interactions': [], 'total': 0},
        )

        assert len(datasets.liana.get(backend='pandas')) == 0
