"""Command-shell backend: run_command via a sentinel-wrapped shell command."""

import base64
import re

import pytest

from webshell_sniper.core.backends import CommandBackend, PHPBackend, get_backend
from webshell_sniper.core.executor import Executor
from webshell_sniper.exceptions import ExecutionFailed


def test_eval_capability_flags():
    assert PHPBackend().supports_eval is True
    assert CommandBackend().supports_eval is False


def test_backend_registry():
    assert isinstance(get_backend("php"), PHPBackend)
    assert isinstance(get_backend("command"), CommandBackend)
    with pytest.raises(ValueError, match="unknown backend"):
        get_backend("ruby")


class CommandShellSim:
    """Simulates a JSP-style command shell: the param is a /bin/sh -c script.

    The executor now base64-wraps the script (``echo B64|base64 -d|sh``), so we
    undo that first, then run the bounded ``echo TOK; cmd; echo TOK`` script.
    """

    def send(self, payload: str) -> str:
        wrap = re.fullmatch(r"echo (\S+)\|base64 -d\|sh", payload)
        if wrap:
            payload = base64.b64decode(wrap.group(1)).decode()
        match = re.match(r"echo (\S+); (.*); echo \1$", payload)
        if not match:
            return ""
        token, cmd = match.group(1), match.group(2)
        out = cmd[5:].split(" 2>&1")[0] if cmd.startswith("echo ") else ""
        return f"{token}{out}{token}"


def test_run_command_on_command_shell():
    ex = Executor(transport=CommandShellSim(), backend=CommandBackend())  # type: ignore[arg-type]
    assert ex.run_command("echo hi") == "hi"


def test_run_php_unsupported_on_command_shell():
    ex = Executor(transport=CommandShellSim(), backend=CommandBackend())  # type: ignore[arg-type]
    with pytest.raises(ExecutionFailed, match="cannot evaluate"):
        ex.run_php("echo 1")
