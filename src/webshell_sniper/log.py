"""Leveled, colored console output built on :mod:`rich`.

Drop-in replacement for the v1 ``core.log.Log`` static class and the
hand-rolled ANSI escapes in ``core/log/color.py``.  Messages are rendered with
:class:`rich.text.Text` (``markup`` disabled) so arbitrary content — paths
containing ``[`` etc. — never gets mis-parsed as markup.
"""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

console = Console()
error_console = Console(stderr=True)


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
