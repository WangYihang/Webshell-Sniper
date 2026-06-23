"""Output renderers — separate *what* is reported from *how* it is shown.

Features and the REPL/CLI describe results (status messages, verbatim output,
tables); a :class:`Renderer` decides the presentation. Three modes ship:

* ``console`` — coloured rich output (the default, interactive feel).
* ``quiet``   — only real output (command results, tables) and errors; the
  ``[+]``/``[!]`` status chatter is suppressed. Good for piping.
* ``json``    — buffer every event and emit one JSON array at :meth:`flush`,
  so non-interactive runs are machine-readable.

This is the seam the ``RENDER`` backlog item calls for; ``log`` simply forwards
to the active renderer, so existing call sites need no change.
"""

from __future__ import annotations

import json as _json
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from typing import Any

from rich.console import Console
from rich.progress import track as _track
from rich.table import Table
from rich.text import Text

# level -> (prefix, rich style, goes-to-stderr)
LEVELS: dict[str, tuple[str, str, bool]] = {
    "info": ("[+]", "bright_magenta", False),
    "warning": ("[!]", "yellow", False),
    "error": ("[-]", "bold red", True),
    "success": ("[+]", "bold green", False),
    "query": ("[?]", "underline cyan", False),
}


class Renderer(ABC):
    name: str = "abstract"

    @abstractmethod
    def message(self, level: str, text: str) -> None: ...

    @abstractmethod
    def raw(self, text: str) -> None: ...

    @abstractmethod
    def table(
        self, columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None
    ) -> None: ...

    def track(self, items: Sequence[Any], description: str = "Working") -> Iterable[Any]:
        return items

    def flush(self) -> None:  # noqa: B027  (optional hook; not all renderers buffer)
        """Emit any buffered output (no-op for streaming renderers)."""


class ConsoleRenderer(Renderer):
    name = "console"

    def __init__(self, console: Console, error_console: Console) -> None:
        self.console = console
        self.error_console = error_console

    def message(self, level: str, text: str) -> None:
        prefix, style, err = LEVELS[level]
        target = self.error_console if err else self.console
        target.print(Text(f"{prefix} {text}", style=style))

    def raw(self, text: str) -> None:
        self.console.print(Text(text))

    def table(
        self, columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None
    ) -> None:
        grid = Table(title=title, header_style="bold cyan")
        for column in columns:
            grid.add_column(str(column), overflow="fold")
        for row in rows:
            grid.add_row(*[str(cell) for cell in row])
        self.console.print(grid)

    def track(self, items: Sequence[Any], description: str = "Working") -> Iterable[Any]:
        return _track(items, description=description, console=self.console)


class QuietRenderer(Renderer):
    """Suppress status chatter; keep real output (raw/tables) and errors."""

    name = "quiet"

    def message(self, level: str, text: str) -> None:
        if LEVELS[level][2]:  # errors only
            print(f"{LEVELS[level][0]} {text}", file=sys.stderr)

    def raw(self, text: str) -> None:
        print(text)

    def table(
        self, columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None
    ) -> None:
        print("\t".join(str(c) for c in columns))
        for row in rows:
            print("\t".join(str(c) for c in row))


class JsonRenderer(Renderer):
    """Buffer events and emit a single JSON array at :meth:`flush`."""

    name = "json"

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def message(self, level: str, text: str) -> None:
        self.events.append({"type": "message", "level": level, "text": text})

    def raw(self, text: str) -> None:
        self.events.append({"type": "output", "text": text})

    def table(
        self, columns: Sequence[str], rows: Iterable[Sequence[object]], title: str | None = None
    ) -> None:
        self.events.append(
            {
                "type": "table",
                "title": title,
                "columns": [str(c) for c in columns],
                "rows": [[str(c) for c in row] for row in rows],
            }
        )

    def flush(self) -> None:
        print(_json.dumps(self.events, indent=2))
        self.events = []


def make_renderer(name: str, console: Console, error_console: Console) -> Renderer:
    if name == "console":
        return ConsoleRenderer(console, error_console)
    if name == "quiet":
        return QuietRenderer()
    if name == "json":
        return JsonRenderer()
    raise ValueError(f"unknown output mode: {name!r}; choose from console, quiet, json")
