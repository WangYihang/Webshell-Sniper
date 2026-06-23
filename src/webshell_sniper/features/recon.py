"""Reconnaissance: enumerate the target's filesystem and PHP configuration.

These are *pure* query functions — they return structured data and never print,
so the REPL/CLI/batch (or a plugin/library caller) decide how to render or store
the results. See the ``PURE`` design note in ``docs/BACKLOG.md``.
"""

from __future__ import annotations

import shlex

from ..core.webshell import WebShell

# Directories worth searching for SUID binaries.
_SUID_PATHS = [
    "/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin",
    "/sbin", "/bin", "/usr/games", "/usr/local/games", "/snap/bin",
]


def _filter_find(output: str) -> list[str]:
    """Drop blank lines and ``find:`` permission-denied noise."""
    return [line for line in output.splitlines() if line and not line.startswith("find:")]


def get_disabled_functions(ws: WebShell) -> set[str]:
    """Return the PHP ``disable_functions`` set (empty if none)."""
    return ws.executor.disabled_functions


def find_writable_dirs(ws: WebShell) -> list[str]:
    """Return writable directories under the webroot."""
    return _filter_find(ws.run_command(f"find {shlex.quote(ws.webroot)} -type d -writable"))


def find_writable_php(ws: WebShell) -> list[str]:
    """Return writable ``.php`` files under the webroot."""
    return _filter_find(ws.run_command(f"find {shlex.quote(ws.webroot)} -name '*.php' -writable"))


def find_config_files(ws: WebShell, keywords: list[str] | None = None) -> list[str]:
    """Return files under the webroot whose names match any of ``keywords``."""
    keywords = keywords or ["config", "db", "database"]
    found: list[str] = []
    for keyword in keywords:
        found.extend(_filter_find(ws.run_command(f"find {shlex.quote(ws.webroot)} -name '*{keyword}*'")))
    return found


def find_suid_binaries(ws: WebShell) -> list[str]:
    """Return SUID-root binaries found across the common bin paths."""
    found: list[str] = []
    for path in _SUID_PATHS:
        found.extend(
            _filter_find(
                ws.run_command(
                    f"find {shlex.quote(path)} -user root -perm -4000 -exec ls -ldb {{}} \\;"
                )
            )
        )
    return found
