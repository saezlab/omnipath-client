"""Session and logging integration via pkg_infra."""

from __future__ import annotations

import logging
from pathlib import Path


_session: object | None = None
_session_initialized = False
_fallback_warning_emitted = False


def get_session(
    workspace: str | Path | None = None,
) -> object | None:
    """Return the pkg_infra session when available.

    Args:
        workspace:
            Workspace path passed to ``pkg_infra.get_session``. Defaults to the
            current working directory.

    Returns:
        The pkg_infra session object, or ``None`` if pkg_infra is unavailable
        or session initialization fails.
    """

    global _session
    global _session_initialized
    global _fallback_warning_emitted

    if _session_initialized:
        return _session

    resolved_workspace = Path(workspace or Path.cwd()).resolve()

    try:
        from pkg_infra import get_session as pkg_get_session

        _session = pkg_get_session(workspace=resolved_workspace)
        _session_initialized = True

    except Exception:  # noqa: BLE001
        _session = None
        _session_initialized = True

        if not _fallback_warning_emitted:
            logging.getLogger(__name__).warning(
                'Failed to initialize pkg_infra session for workspace %s; '
                'falling back to standard library logging.',
                resolved_workspace,
                exc_info=True,
            )
            _fallback_warning_emitted = True

    return _session


_logger: logging.Logger | None = None


def get_logger(name: str = 'omnipath_client') -> logging.Logger:
    """Return a logger backed by pkg_infra logging when available.

    Args:
        name:
            Logger name, typically ``__name__`` from the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """

    global _logger

    if _logger is None:
        get_session()
        _logger = logging.getLogger('omnipath_client')
        _logger.addHandler(logging.NullHandler())

    return logging.getLogger(name)
