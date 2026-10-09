"""Offline tests for ``lookup()`` on the Postgres database service."""

from __future__ import annotations

import pytest

from omnipath_client._client import OmniPath, _is_pk, _term_code_first


pl = pytest.importorskip('polars')


CAFFEINE_PK = 'fbe79ce0-27bf-9c0f-0105-3b8b4b6554b1'

RESOLVE = {
    'matches': [
        {'identifier': 'caffeine', 'entityPks': [CAFFEINE_PK]},
    ],
}

BY_PKS = {
    'entities': [
        {
            'entityPk': CAFFEINE_PK,
            'canonicalIdentifier': 'RYYVLZVUVIJVGH-UHFFFAOYSA-N',
            'canonicalIdentifierType': 'Standard Inchi Key:MI:1101',
            'entityType': 'Chemical:OM:0037',
            'taxonomyId': None,
            'sources': ['chebi', 'hmdb'],
            'identifiers': [
                {'identifier': 'caffeine', 'identifierType': 'Name:OM:0202'},
                {'identifier': '27732', 'identifierType': 'Chebi:MI:0474'},
                {'identifier': '3295', 'identifierType': 'Chebi:MI:0474'},
                {'identifier': 'HMDB0001847', 'identifierType': 'Hmdb:OM:0004'},
                {'identifier': 'CHEMBL113', 'identifierType': 'Chembl Compound:MI:0967'},
            ],
        },
    ],
}


def _fake_fetch(endpoint, backend = None, **params):

    if endpoint == 'entities/resolve':
        return RESOLVE

    if endpoint == 'entities/by-pks':
        assert params == {'entityPks': [CAFFEINE_PK]}
        return BY_PKS

    raise AssertionError(f'unexpected endpoint: {endpoint}')


@pytest.fixture
def client(monkeypatch):

    c = OmniPath.__new__(OmniPath)
    monkeypatch.setattr(c, '_fetch', _fake_fetch, raising = False)
    monkeypatch.setattr(c, 'resolve', lambda ids: RESOLVE, raising = False)

    return c


def test_term_code_first():

    assert _term_code_first('Chebi:MI:0474') == 'MI:0474:Chebi'
    assert _term_code_first('Standard Inchi Key:MI:1101') == (
        'MI:1101:Standard Inchi Key'
    )
    assert _term_code_first('omnipath:complex_member_hash') == (
        'omnipath:complex_member_hash'
    )
    assert _term_code_first(None) is None


def test_is_pk():

    assert _is_pk(CAFFEINE_PK)
    assert _is_pk(42)
    assert _is_pk('42')
    assert not _is_pk('caffeine')


def test_lookup_uuid_keys(client):

    df = client.lookup('caffeine', id_types = ['name', 'chebi', 'hmdb', 'chembl'])

    assert df.height == 1
    row = df.row(0, named = True)
    assert row['entity_pk'] == CAFFEINE_PK
    assert row['query'] == 'caffeine'
    assert row['entity_type'] == 'OM:0037:Chemical'
    assert row['name'] == 'caffeine'
    assert row['chebi'] == '3295'  # the shortest value wins
    assert row['hmdb'] == 'HMDB0001847'
    assert row['chembl'] == 'CHEMBL113'


def test_lookup_no_match(client, monkeypatch):

    monkeypatch.setattr(client, 'resolve', lambda ids: {'matches': []})

    df = client.lookup('nothing-like-this', id_types = ['name'])

    assert df.height == 0
    assert 'name' in df.columns
