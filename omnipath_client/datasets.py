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

"""
The registered datasets, one attribute each.

``datasets.liana`` and ``datasets.metalinksdb`` are not written down
anywhere in this module. A dataset is a row in the service's registry, so
the names are read from the service and turned into attributes here --
which means a build that registers a new dataset serves it through this
module without the client being changed or reinstalled.

    >>> import omnipath_client as op
    >>> op.set_base_url('https://dev3.omnipathdb.org/api')
    >>> op.datasets.names()
    ['liana', 'metalinksdb']
    >>> op.datasets.liana.get(limit=100)   # a DataFrame
    >>> op.datasets.liana.info()           # what it is made of
    >>> op.datasets.liana.stats()          # how much of it there is

Each accessor is a thin view of the general interactions API: ``get`` is
``interaction_dataset``, ``stats`` is ``interaction_stats`` scoped to the
one name, and ``info`` is that name's row of ``interaction_parameters``.
Anything the dataset accessors do not reach -- composing two datasets,
excluding a resource, filtering on an annotation -- is reached through
those functions directly.
"""

from __future__ import annotations

__all__ = ['Dataset', 'names', 'info', 'get']

from typing import Any

from omnipath_client._types import BackendType
from omnipath_client._client import (
    _get_default,
    interaction_stats,
    interaction_dataset,
    interaction_parameters,
)
from omnipath_client._errors import OmniPathError
from omnipath_client._session import get_logger
from omnipath_client._response import to_frame


logger = get_logger(__name__)

# The key the parameter surface files the registry under.
_PARAMETER = 'datasets'

# The key each page of interactions carries its rows under.
_ROWS = 'interactions'


def _registry() -> dict[str, dict[str, Any]]:
    """Every registered dataset, by name.

    Read from the service on each call rather than cached, because the
    registry belongs to the build being served and a client that cached
    it would answer for a build that had since been replaced.

    Returns:
        The registry rows, keyed by dataset name.
    """

    surface = interaction_parameters()
    entry = surface.get('parameters', {}).get(_PARAMETER, {})

    return {
        row['value']: row
        for row in entry.get('values', [])
        if 'value' in row
    }


def names() -> list[str]:
    """The datasets this service registers.

    Returns:
        The registered names, in the order the service reports them.
    """

    return list(_registry())


def info(dataset: str | None = None) -> Any:
    """What a dataset is made of, as the registry declares it.

    Args:
        dataset:
            A dataset name. Without one, every registered dataset is
            described.

    Returns:
        The registry row for that dataset, or a list of every row.

    Raises:
        OmniPathError:
            If the service registers no dataset under this name.
    """

    registry = _registry()

    if dataset is None:

        return list(registry.values())

    if dataset not in registry:

        raise OmniPathError(
            f'No dataset named {dataset!r} on '
            f'{_get_default()._base_url}. '
            f'Registered: {sorted(registry)}',
        )

    return registry[dataset]


def get(
    dataset: str,
    backend: BackendType = 'auto',
    limit: int = 50,
    **params: Any,
) -> Any:
    """One dataset's interactions, as a DataFrame.

    Args:
        dataset:
            A registered dataset name.
        backend:
            DataFrame backend, or ``'auto'`` for the first installed.
        limit:
            Rows to fetch. The service pages, so a large number is a
            large request rather than a stream.
        **params:
            Anything else ``interaction_dataset`` accepts, such as
            ``organism``, ``resources``, ``view`` or ``cursor``.

    Returns:
        A DataFrame of the interactions on that page.
    """

    page = interaction_dataset(dataset, limit=limit, **params)

    logger.info(
        'Dataset %s returned %d row(s) of about %s',
        dataset,
        len(page.get(_ROWS, [])),
        page.get('total'),
    )

    return to_frame(page.get(_ROWS, []), backend=backend)


class Dataset:
    """One registered dataset, and the three questions asked of it.

    Args:
        name:
            The name the service registers this dataset under. It is
            not checked here: the service holds the registry, and it
            answers for a name it does not know.
    """

    def __init__(self, name: str) -> None:

        self.name = name

    def __repr__(self) -> str:

        return f'<Dataset {self.name}>'

    def get(
        self,
        backend: BackendType = 'auto',
        limit: int = 50,
        **params: Any,
    ) -> Any:
        """This dataset's interactions, as a DataFrame.

        See ``omnipath_client.datasets.get`` for the arguments.
        """

        return get(self.name, backend=backend, limit=limit, **params)

    def info(self) -> dict[str, Any]:
        """What this dataset is made of.

        Returns:
            Its registry row: contributing resources, the interaction
            classes it is restricted to, the attributes it projects by
            default and the ones it always carries, its collapse mode,
            and -- for an assembled dataset -- the composition it is
            built by.
        """

        return info(self.name)

    def stats(self, **scope: Any) -> dict[str, Any]:
        """How much this dataset holds, without fetching any of it.

        Args:
            **scope:
                Further restrictions, as ``interaction_stats`` takes
                them. Without any, the whole dataset is described.

        Returns:
            A dict with ``total``, ``total_is_estimate`` and
            ``by_resource``.
        """

        return interaction_stats(datasets=self.name, **scope)

    def resources(self) -> list[str]:
        """The resources contributing to this dataset.

        Returns:
            Their names, as the registry lists them.
        """

        return list(self.info().get('included_sources') or [])

    def attributes(self) -> list[str]:
        """The attributes this dataset projects.

        Returns:
            The default attributes together with the ones the dataset
            always carries.
        """

        row = self.info()
        declared = list(row.get('default_attributes') or [])

        for name in row.get('mandatory_attributes') or []:
            if name not in declared:
                declared.append(name)

        return declared


def __getattr__(name: str) -> Dataset:
    """Serve a registered dataset name as an attribute of this module.

    Args:
        name:
            The attribute asked for.

    Returns:
        The dataset of that name.

    Raises:
        AttributeError:
            If the service registers no such dataset. The message lists
            what it does register, because the usual cause is a name
            this build does not carry rather than a typo.
    """

    if name.startswith('_'):

        raise AttributeError(name)

    registered = names()

    if name not in registered:

        raise AttributeError(
            f'No dataset named {name!r} on {_get_default()._base_url}. '
            f'Registered: {sorted(registered)}',
        )

    return Dataset(name)


def __dir__() -> list[str]:
    """List the datasets alongside this module's own names.

    Returns:
        The names, so that tab completion offers the datasets the
        service actually carries.
    """

    try:
        registered = names()

    except Exception:  # noqa: BLE001
        logger.warning(
            'Could not read the dataset registry for completion',
            exc_info=True,
        )
        registered = []

    return sorted({*__all__, *registered})
