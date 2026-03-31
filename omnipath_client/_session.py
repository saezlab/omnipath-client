"""Session, configuration, and logging via pkg_infra (saezlab_core).

Until pkg_infra supports per-package config sections, this module
provides a lightweight logging setup using the standard library.
"""

from __future__ import annotations

import logging


_logger: logging.Logger | None = None


def get_logger(name: str = 'omnipath_client') -> logging.Logger:
    """Return a logger for the given module name.

    Args:
        name:
            Logger name, typically ``__name__`` from the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """

    global _logger

    if _logger is None:
        _logger = logging.getLogger('omnipath_client')
        _logger.addHandler(logging.NullHandler())

    return logging.getLogger(name)
