"""Leveled console output that forwards to a swappable :class:`Renderer`.

Public functions (``info``/``warning``/``error``/``success``/``query``/``raw``/
``table``/``track``) are unchanged call sites; *how* they render is decided by
the active renderer (``console`` / ``quiet`` / ``json`` — see :mod:`render`).
Debug tracing (``--debug``) still uses stdlib logging onto rich.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

from rich.console import Console

from .render import ConsoleRenderer, Renderer, make_renderer

console = Console()
error_console = Console(stderr=True)

_logger = logging.getLogger("webshell_sniper")
_debug_enabled = False

_renderer: Renderer = ConsoleRenderer(console, error_console)


def set_renderer(name: str) -> None:
    """Switch output mode (``console`` / ``quiet`` / ``json``)."""
    global _renderer
    _renderer = make_renderer(name, console, error_console)


def get_renderer() -> Renderer:
    return _renderer


def flush() -> None:
    """Emit any buffered output (e.g. the JSON renderer's accumulated events)."""
    _renderer.flush()


def set_debug(enabled: bool) -> None:
    """Enable/disable `--debug` tracing of payloads and raw responses."""
    global _debug_enabled
    _debug_enabled = enabled
    if enabled and not _logger.handlers:
        from rich.logging import RichHandler

        _logger.addHandler(RichHandler(console=error_console, show_path=False, markup=False))
        _logger.setLevel(logging.DEBUG)


def debug(message: object) -> None:
    if _debug_enabled:
        _logger.debug(str(message))


def info(message: object) -> None:
    _renderer.message("info", str(message))


def warning(message: object) -> None:
    _renderer.message("warning", str(message))


def error(message: object) -> None:
    _renderer.message("error", str(message))


def success(message: object) -> None:
    _renderer.message("success", str(message))


def query(message: object) -> None:
    _renderer.message("query", str(message))


def raw(message: object) -> None:
    """Print server output verbatim, without a prefix or markup parsing."""
    _renderer.raw(str(message))


def table(
    columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None
) -> None:
    """Render tabular data (e.g. SQL results, schema listings)."""
    _renderer.table(columns, rows, title)


def track[T](items: Sequence[T], description: str = "Working") -> Iterable[T]:
    """Wrap a sequence in a progress bar (used for multi-file transfers)."""
    return _renderer.track(items, description)
