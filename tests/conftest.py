"""
Shared test fixtures for omnipath-client tests.
"""

from pathlib import Path

import pytest


SAMPLES_DIR = Path(__file__).parent.parent / 'parquet-samples'


@pytest.fixture
def entities_parquet():
    """
    Path to the sample entities Parquet file.
    """

    return SAMPLES_DIR / 'search_entities.parquet'


@pytest.fixture
def interactions_parquet():
    """
    Path to the sample interactions Parquet file.
    """

    return SAMPLES_DIR / 'search_interactions.parquet'


@pytest.fixture
def associations_parquet():
    """
    Path to the sample associations Parquet file.
    """

    return SAMPLES_DIR / 'search_associations.parquet'
