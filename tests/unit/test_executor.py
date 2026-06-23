"""Executor logic without a network: a fake transport simulates PHP echoing."""

import base64
import re

import pytest

from webshell_sniper.core.executor import Executor
from webshell_sniper.exceptions import ExecutionFailed, NoExecFunction


class FakeTransport:
    """Mimics a webshell: decode the eval payload and echo back the sentinels."""

    def __init__(self):
        self.last_inner = ""

    def send(self, php_code: str) -> str:
        match = re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", php_code)
        assert match, f"unexpected payload shape: {php_code}"
        inner = base64.b64decode(match.group(1)).decode()
        self.last_inner = inner
        # inner == "echo 'TOKEN';<code>;echo 'TOKEN';"
        token = inner.split("'", 2)[1]
        return f"{token}<<SIMULATED>>{token}"


def test_run_php_unwraps_sentinels():
    ex = Executor(FakeTransport())  # type: ignore[arg-type]
    assert ex.run_php("echo 1") == "<<SIMULATED>>"


def test_run_php_raises_without_sentinels():
    class Broken:
        def send(self, _):
            return "no sentinels here"

    with pytest.raises(ExecutionFailed):
        Executor(Broken()).run_php("echo 1")  # type: ignore[arg-type]


def test_run_command_base64s_command_with_stderr_merge():
    transport = FakeTransport()
    ex = Executor(transport)  # type: ignore[arg-type]
    ex._disabled = set()  # system available
    ex.run_command("id")
    # The inner PHP must reference system() and carry base64("id 2>&1").
    assert "system(" in transport.last_inner
    assert base64.b64encode(b"id 2>&1").decode() in transport.last_inner


@pytest.mark.parametrize(
    ("disabled", "expected"),
    [
        (set(), "system"),
        ({"system"}, "passthru"),
        ({"system", "passthru"}, "shell_exec"),
        ({"system", "passthru", "shell_exec"}, "exec"),
        ({"system", "passthru", "shell_exec", "exec"}, "popen"),
    ],
)
def test_exec_function_fallback_order(disabled, expected):
    ex = Executor(FakeTransport())  # type: ignore[arg-type]
    ex._disabled = disabled
    assert ex.pick_exec_function() == expected


def test_all_disabled_raises():
    ex = Executor(FakeTransport())  # type: ignore[arg-type]
    ex._disabled = {"system", "passthru", "shell_exec", "exec", "popen", "proc_open"}
    with pytest.raises(NoExecFunction):
        ex.pick_exec_function()
