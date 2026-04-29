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
    'entities',
    'relations',
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
]

from omnipath_client import cosmos, utils
from ._client import (
    OmniPath,
    params,
    values,
    entities,
    resolve,
    endpoints,
    relations,
    resources,
    annotations,
    ontologies,
    search_terms,
    ontology_tree,
    ontology_terms,
    entities_slice,
    relations_slice,
)
from ._metadata import __author__, __version__
