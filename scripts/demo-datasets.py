#!/usr/bin/env python

"""
Reach LIANA and MetaLinksDB as DataFrames, from a chosen deployment.

    python scripts/demo-datasets.py
    python scripts/demo-datasets.py https://dev.omnipathdb.org/api

The datasets are new, so the default here is the development deployment
that serves them, not the production one.
"""

import sys

import omnipath_client as op


DEFAULT_URL = 'https://dev3.omnipathdb.org/api'


def main(url: str) -> None:
    """Show each dataset the service carries.

    Args:
        url:
            Base URL of the API to address.
    """

    op.set_base_url(url)
    print(f'service:  {op.base_url()}')

    registered = op.datasets.names()
    print(f'datasets: {registered}\n')

    for name in registered:

        dataset = getattr(op.datasets, name)
        stats = dataset.stats()
        total = stats['total']
        qualifier = 'about' if stats['total_is_estimate'] else 'exactly'

        print(f'--- {name} ---')
        print(f'interactions: {qualifier} {total:,}')
        resources = dataset.resources()
        shown = ', '.join(resources[:4])
        more = '...' if len(resources) > 4 else ''
        print(f'resources:    {len(resources)} ({shown}{more})')
        print(f'attributes:   {dataset.attributes()}')

        frame = dataset.get(limit=5)
        print(f'frame:        {type(frame).__module__.split(".")[0]}, '
              f'{frame.shape[0]} rows x {frame.shape[1]} columns')
        print(frame[['source_label', 'target_label', 'interaction_type']])
        print()


if __name__ == '__main__':

    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL)
