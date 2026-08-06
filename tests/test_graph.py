"""Tests for turning an OmniPath table into an AnnNet graph."""

from __future__ import annotations

import pytest


annnet = pytest.importorskip('annnet')
pl = pytest.importorskip('polars')

from omnipath_client._graph import to_annnet, annotate_nodes  # noqa: E402


# -- Sample tables ----------------------------------------------------------

INTERACTIONS = [
    {
        'source': 'EGFR',
        'target': 'STAT3',
        'is_directed': True,
        'consensus_weight': 1.0,
        'references': 'PMID:1',
    },
    {
        'source': 'TP53',
        'target': 'MDM2',
        'is_directed': False,
        'consensus_weight': 2.5,
        'references': 'PMID:2',
    },
]

RELATIONS = [
    {
        'subject_entity_pk': 101,
        'object_entity_pk': 202,
        'relation_pk': 1,
        'predicate': 'activates',
    },
    {
        'subject_entity_pk': 202,
        'object_entity_pk': 303,
        'relation_pk': 2,
        'predicate': 'inhibits',
    },
]

ANNOTATIONS = [
    {
        'genesymbol': 'EGFR',
        'source': 'HGNC',
        'label': 'family',
        'value': 'kinase',
    },
    {
        'genesymbol': 'EGFR',
        'source': 'HGNC',
        'label': 'family',
        'value': 'receptor',
    },
    {'genesymbol': 'STAT3', 'source': 'HGNC', 'label': 'family', 'value': 'tf'},
    {
        'genesymbol': 'STAT3',
        'source': 'UniProt_location',
        'label': 'location',
        'value': 'nucleus',
    },
    {
        'genesymbol': 'NOTHERE',
        'source': 'HGNC',
        'label': 'family',
        'value': 'other',
    },
]


@pytest.fixture
def interactions():
    return pl.DataFrame(INTERACTIONS)


@pytest.fixture
def relations():
    return pl.DataFrame(RELATIONS)


# -- Building the graph -----------------------------------------------------


def test_an_interaction_table_becomes_a_graph(interactions):
    graph = to_annnet(interactions)
    assert graph.ncount() == 4
    assert graph.ecount() == 2
    assert set(graph.N) == {'EGFR', 'STAT3', 'TP53', 'MDM2'}


def test_the_relations_export_names_its_endpoints_by_primary_key(relations):
    graph = to_annnet(relations)
    assert set(graph.N) == {'101', '202', '303'}
    assert set(graph.E) == {'1', '2'}


def test_every_column_that_names_no_structure_becomes_an_edge_attribute(
    interactions,
):
    graph = to_annnet(interactions)
    assert list(graph.E['references']) == ['PMID:1', 'PMID:2']


def test_the_direction_and_the_weight_come_off_their_columns(interactions):
    graph = to_annnet(interactions)
    first, second = (graph.get_edge(edge_id) for edge_id in graph.E)
    assert (first.directed, first.weight) == (True, 1.0)
    assert (second.directed, second.weight) == (False, 2.5)


def test_a_row_that_names_no_endpoint_is_skipped():
    table = pl.DataFrame(
        {'source': ['A', 'B'], 'target': ['C', None]},
    )
    graph = to_annnet(table)
    assert graph.ecount() == 1


def test_a_row_that_names_no_endpoint_raises_when_the_caller_asks():
    table = pl.DataFrame({'source': ['A', 'B'], 'target': ['C', None]})
    with pytest.raises(ValueError, match='names no endpoint'):
        to_annnet(table, dropna=False)


def test_a_table_whose_endpoints_cannot_be_told_apart_raises():
    table = pl.DataFrame({'left': ['A'], 'right': ['B']})
    with pytest.raises(ValueError, match='names an endpoint'):
        to_annnet(table)


def test_the_caller_may_name_the_columns():
    table = pl.DataFrame({'left': ['A'], 'right': ['B'], 'note': ['x']})
    graph = to_annnet(table, source_col='left', target_col='right')
    assert set(graph.N) == {'A', 'B'}
    assert list(graph.E['note']) == ['x']


def test_the_caller_may_choose_which_columns_become_attributes(interactions):
    graph = to_annnet(interactions, edge_attr_cols=[])
    with pytest.raises(KeyError):
        graph.E['references']


def test_a_slice_column_places_each_edge():
    table = pl.DataFrame(
        {
            'source': ['A', 'B'],
            'target': ['B', 'C'],
            'slice': ['early', 'late'],
        },
    )
    graph = to_annnet(table)
    assert set(graph.slices.list()) >= {'early', 'late'}


def test_an_empty_table_gives_an_empty_graph():
    graph = to_annnet(pl.DataFrame({'source': [], 'target': []}))
    assert graph.ncount() == 0
    assert graph.ecount() == 0


@pytest.mark.parametrize('backend', ['pandas', 'pyarrow'])
def test_the_table_may_come_from_any_backend(backend, interactions):
    pytest.importorskip(backend)
    native = (
        interactions.to_pandas()
        if backend == 'pandas'
        else interactions.to_arrow()
    )
    graph = to_annnet(native)
    assert graph.ecount() == 2


# -- Annotating the nodes ---------------------------------------------------


def test_annotations_land_on_the_nodes_the_graph_holds(interactions):
    graph = to_annnet(interactions)
    annotate_nodes(graph, pl.DataFrame(ANNOTATIONS))
    assert (
        graph.attrs.get_attr_vertex('STAT3', 'UniProt_location:location')
        == 'nucleus'
    )
    assert 'NOTHERE' not in set(graph.N)


def test_a_pair_with_several_values_joins_them_in_a_stable_order(interactions):
    graph = to_annnet(interactions)
    annotate_nodes(graph, pl.DataFrame(ANNOTATIONS))
    assert (
        graph.attrs.get_attr_vertex('EGFR', 'HGNC:family') == 'kinase;receptor'
    )


def test_the_caller_may_ask_for_some_resources_only(interactions):
    graph = to_annnet(interactions)
    annotate_nodes(
        graph, pl.DataFrame(ANNOTATIONS), sources=['UniProt_location']
    )
    assert (
        graph.attrs.get_attr_vertex('STAT3', 'UniProt_location:location')
        == 'nucleus'
    )
    assert graph.attrs.get_attr_vertex('EGFR', 'HGNC:family') is None


def test_annotating_returns_the_same_graph(interactions):
    graph = to_annnet(interactions)
    assert annotate_nodes(graph, pl.DataFrame(ANNOTATIONS)) is graph


def test_the_annotations_may_arrive_on_any_backend(interactions):
    pytest.importorskip('pandas')
    graph = to_annnet(interactions)
    annotate_nodes(graph, pl.DataFrame(ANNOTATIONS).to_pandas())
    assert (
        graph.attrs.get_attr_vertex('EGFR', 'HGNC:family') == 'kinase;receptor'
    )


# -- The public surface -----------------------------------------------------


def test_the_package_exports_the_three_functions():
    import omnipath_client as oc

    for name in ('to_annnet', 'annotate_nodes', 'node_annotations'):
        assert name in oc.__all__
        assert callable(getattr(oc, name))


def test_the_broken_stub_is_gone():
    import omnipath_client._graph as graph_module

    assert not hasattr(graph_module, 'relations_to_graph')


def test_building_a_graph_without_annnet_says_what_to_install():
    import sys

    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if key == 'annnet' or key.startswith('annnet.')
    }
    sys.modules['annnet'] = None
    try:
        with pytest.raises(ImportError, match='annnet is required'):
            to_annnet(pl.DataFrame({'source': ['A'], 'target': ['B']}))
    finally:
        sys.modules.pop('annnet', None)
        sys.modules.update(saved)
