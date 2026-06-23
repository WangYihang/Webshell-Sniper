"""Leveled, colored console output built on :mod:`rich`.

Drop-in replacement for the v1 ``core.log.Log`` static class and the
hand-rolled ANSI escapes in ``core/log/color.py``.  Messages are rendered with
:class:`rich.text.Text` (``markup`` disabled) so arbitrary content — paths
containing ``[`` etc. — never gets mis-parsed as markup.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import TypeVar

from rich.console import Console
from rich.progress import track as _track
from rich.table import Table
from rich.text import Text

console = Console()
error_console = Console(stderr=True)

_T = TypeVar("_T")

_logger = logging.getLogger("webshell_sniper")
_debug_enabled = False


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


def _emit(prefix: str, message: object, style: str, *, err: bool = False) -> None:
    text = Text(f"{prefix} {message}", style=style)
    (error_console if err else console).print(text)


def info(message: object) -> None:
    _emit("[+]", message, "bright_magenta")


def warning(message: object) -> None:
    _emit("[!]", message, "yellow")


def error(message: object) -> None:
    _emit("[-]", message, "bold red", err=True)


def success(message: object) -> None:
    _emit("[+]", message, "bold green")


def query(message: object) -> None:
    _emit("[?]", message, "underline cyan")


def raw(message: object) -> None:
    """Print server output verbatim, without a prefix or markup parsing."""
    console.print(Text(str(message)))


def table(columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None) -> None:
    """Render tabular data (e.g. SQL results, schema listings)."""
    grid = Table(title=title, header_style="bold cyan")
    for column in columns:
        grid.add_column(str(column), overflow="fold")
    for row in rows:
        grid.add_row(*[str(cell) for cell in row])
    console.print(grid)


def track(items: Sequence[_T], description: str = "Working") -> Iterable[_T]:
    """Wrap a sequence in a progress bar (used for multi-file transfers)."""
    return _track(items, description=description, console=console)
