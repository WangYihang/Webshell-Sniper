"""Reconnaissance: enumerate the target's filesystem and PHP configuration."""

from __future__ import annotations

import shlex

from .. import log
from ..core.webshell import WebShell

# Directories worth searching for SUID binaries.
_SUID_PATHS = [
    "/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin",
    "/sbin", "/bin", "/usr/games", "/usr/local/games", "/snap/bin",
]


def get_disabled_functions(ws: WebShell) -> set[str]:
    disabled = ws.executor.disabled_functions
    if disabled:
        log.success("Disabled functions:\n" + "\n".join(f"\t[{f}]" for f in sorted(disabled)))
    else:
        log.warning("No PHP functions are disabled.")
    return disabled


def find_writable_dirs(ws: WebShell) -> list[str]:
    """Return writable directories under the webroot."""
    output = ws.run_command(f"find {shlex.quote(ws.webroot)} -type d -writable")
    dirs = [line for line in output.splitlines() if line and not line.startswith("find:")]
    if dirs:
        log.success("Writable directories:\n" + "\n".join(f"\t[{d}]" for d in dirs))
    else:
        log.warning("No writable directories found.")
    return dirs


def find_writable_php(ws: WebShell) -> list[str]:
    output = ws.run_command(f"find {shlex.quote(ws.webroot)} -name '*.php' -writable")
    files = [line for line in output.splitlines() if line and not line.startswith("find:")]
    if files:
        log.success("Writable PHP files:\n" + "\n".join(f"\t[{f}]" for f in files))
    else:
        log.warning("No writable PHP files found.")
    return files


def find_config_files(ws: WebShell, keywords: list[str] | None = None) -> list[str]:
    keywords = keywords or ["config", "db", "database"]
    found: list[str] = []
    for keyword in keywords:
        log.info(f"Searching for files matching *{keyword}* ...")
        output = ws.run_command(f"find {shlex.quote(ws.webroot)} -name '*{keyword}*'")
        hits = [line for line in output.splitlines() if line and not line.startswith("find:")]
        found.extend(hits)
        if hits:
            log.success("\n".join(f"\t[{h}]" for h in hits))
        else:
            log.warning("Nothing found.")
    return found


def find_suid_binaries(ws: WebShell) -> list[str]:
    found: list[str] = []
    for path in _SUID_PATHS:
        output = ws.run_command(
            f"find {shlex.quote(path)} -user root -perm -4000 -exec ls -ldb {{}} \\;"
        )
        hits = [line for line in output.splitlines() if line and not line.startswith("find:")]
        if hits:
            found.extend(hits)
            log.success(f"{path}:\n" + "\n".join(f"\t{h}" for h in hits))
    if not found:
        log.warning("No SUID binaries found.")
    return found
