#!/usr/bin/env python

#
# This file is part of the `omnipath_client` Python module
#
# Copyright 2026
# Heidelberg University Hospital
#
# File author(s): OmniPath Team (omnipathdb@gmail.com)
#
# Distributed under the BSD-3-Clause license
# See the file `LICENSE` or read a copy at
# https://opensource.org/license/bsd-3-clause
#

"""The new implementation for the OmniPath Python client."""

__all__ = [
    '__version__',
    '__author__',
    'OmniPath',
    'datasets',
    'set_base_url',
    'base_url',
    'entities',
    'relations',
    'interactions',
    'interaction_dataset',
    'interactions_compose',
    'interaction_parameters',
    'interaction_stats',
    'annotations',
    'resolve',
    'entities_slice',
    'relations_slice',
    'resources',
    'ontology_terms',
    'ontology_tree',
    'search_terms',
    'ontologies',
    'endpoints',
    'params',
    'values',
    'lookup',
    'related',
    'cache_clear',
    'fresh',
    'logfile',
    'log',
    'to_annnet',
    'annotate_nodes',
    'node_annotations',
]

from omnipath_client import cosmos, utils, datasets
from omnipath_client._graph import (
    to_annnet,
    annotate_nodes,
    node_annotations,
)
from omnipath_client._session import logfile
from omnipath_client._session import open_log as log
from ._client import (
    OmniPath,
    base_url,
    set_base_url,
    fresh,
    lookup,
    params,
    values,
    related,
    entities,
    resolve,
    endpoints,
    relations,
    resources,
    interactions,
    interaction_stats,
    interaction_dataset,
    interactions_compose,
    interaction_parameters,
    annotations,
    ontologies,
    cache_clear,
    search_terms,
    ontology_tree,
    ontology_terms,
    entities_slice,
    relations_slice,
)
from ._metadata import __author__, __version__
