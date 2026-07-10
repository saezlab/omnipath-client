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


def _active_log_files() -> list[Path]:
    """Collect ``FileHandler`` destinations from the logging tree (fallback)."""

    handlers: list[logging.Handler] = list(logging.getLogger().handlers)

    for obj in logging.Logger.manager.loggerDict.values():
        if isinstance(obj, logging.Logger):
            handlers.extend(obj.handlers)

    seen: dict[str, Path] = {}

    for handler in handlers:
        base = getattr(handler, 'baseFilename', None)
        if base and base not in seen:
            seen[base] = Path(base)

    return list(seen.values())


def logfile() -> Path | None:
    """Return the path of the current log file, or ``None`` if none is active.

    Ensures logging is initialized, then delegates to ``pkg_infra``. Falls back
    to inspecting the standard logging handlers when ``pkg_infra`` is
    unavailable or too old to provide the helper.
    """

    get_logger()

    try:
        from pkg_infra import logfile as _pkg_logfile

        return _pkg_logfile()

    except (ImportError, AttributeError):
        files = _active_log_files()
        existing = [path for path in files if path.exists()]

        if existing:
            return max(existing, key=lambda path: path.stat().st_mtime)

        return files[0] if files else None


def open_log(
    path: str | Path | None = None,
    pager: str | None = None,
) -> Path | None:
    """Open the current (or given) log file in a terminal pager.

    Args:
        path: Log file to open. Defaults to :func:`logfile`.
        pager: Pager command. Defaults to ``$PAGER`` or ``less``.

    Returns:
        The path that was opened, or ``None`` when no log file is available.
    """

    get_logger()

    try:
        from pkg_infra import open_log as _pkg_open_log

        return _pkg_open_log(path=path, pager=pager)

    except (ImportError, AttributeError):
        import os
        import shutil
        import subprocess

        target = Path(path) if path is not None else logfile()

        if target is None:
            return None

        if not target.exists():
            print(target)
            return target

        pager_cmd = (pager or os.environ.get('PAGER') or 'less').split()

        if shutil.which(pager_cmd[0]) is None:
            print(target)
            return target

        subprocess.run([*pager_cmd, str(target)], check=False)  # noqa: S603

        return target
