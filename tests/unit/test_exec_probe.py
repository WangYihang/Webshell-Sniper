"""Executor probes the chosen exec function and falls back if it's broken."""

import base64
import re

from webshell_sniper.core.executor import Executor


class ShellSim:
    """Simulates a shell where only ``working`` exec functions produce output.

    Models the real-world case where e.g. ``system`` is *not* in
    ``disable_functions`` but is silently neutered (suhosin/open_basedir), so it
    returns nothing.
    """

    def __init__(self, working: set[str]):
        self.working = working

    def send(self, php_code: str) -> str:
        inner = base64.b64decode(
            re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", php_code).group(1)
        ).decode()
        token = inner.split("'", 2)[1]
        body = inner[len(f"echo '{token}';") : -len(f"echo '{token}';")]
        return f"{token}{self._run(body)}{token}"

    def _run(self, body: str) -> str:
        match = re.search(
            r"(system|passthru|shell_exec|exec|popen|proc_open)\(base64_decode\('([^']*)'\)", body
        )
        if not match or match.group(1) not in self.working:
            return ""
        cmd = base64.b64decode(match.group(2)).decode()
        echoed = re.match(r"echo (\S+)", cmd)
        return echoed.group(1) if echoed else "OK"


def test_skips_silently_broken_function():
    ex = Executor(ShellSim(working={"shell_exec", "exec"}))
    ex._disabled = set()  # nothing disabled -> system would be picked first
    assert ex._resolve_exec_function() == "shell_exec"  # system/passthru echo nothing


def test_respects_disabled_then_probes():
    ex = Executor(ShellSim(working={"exec"}))
    ex._disabled = {"system"}  # disabled; passthru/shell_exec enabled-but-broken
    assert ex._resolve_exec_function() == "exec"


def test_run_command_uses_a_working_function():
    ex = Executor(ShellSim(working={"shell_exec"}))
    ex._disabled = set()
    assert ex.run_command("echo marker") == "marker"


def test_falls_back_to_first_when_probe_inconclusive():
    # No function echoes the probe -> fall back to the first non-disabled one.
    ex = Executor(ShellSim(working=set()))
    ex._disabled = {"system"}
    assert ex._resolve_exec_function() == "passthru"
