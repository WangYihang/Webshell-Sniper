"""Executor filesystem primitives: PHP eval path + POSIX command fallback."""

import base64
import re

from webshell_sniper.core.backends import CommandBackend, PHPBackend
from webshell_sniper.core.executor import Executor


class PHPTransport:
    """Decodes the eval payload and returns a programmed reply between sentinels."""

    def __init__(self, reply: str = ""):
        self.reply = reply
        self.inner = ""

    def send(self, payload: str) -> str:
        match = re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", payload)
        assert match, f"unexpected payload: {payload}"
        self.inner = base64.b64decode(match.group(1)).decode()
        token = self.inner.split("'", 2)[1]
        return f"{token}{self.reply}{token}"


class CommandTransport:
    """Mimics a command-only shell: ``echo TOK; <cmd>; echo TOK``."""

    def __init__(self, reply: str = ""):
        self.reply = reply
        self.cmd = ""

    def send(self, payload: str) -> str:
        # payload == "echo TOK; <cmd> 2>&1; echo TOK"
        token = payload.split(";", 1)[0].replace("echo ", "").strip()
        self.cmd = payload
        return f"{token}{self.reply}{token}"


def _php_exec(reply: str) -> tuple[Executor, PHPTransport]:
    t = PHPTransport(reply)
    ex = Executor(t, backend=PHPBackend())  # type: ignore[arg-type]
    ex._disabled = set()
    return ex, t


def _cmd_exec(reply: str) -> tuple[Executor, CommandTransport]:
    t = CommandTransport(reply)
    ex = Executor(t, backend=CommandBackend())  # type: ignore[arg-type]
    return ex, t


# -- PHP eval path ------------------------------------------------------------
def test_php_fs_exists_parses_one():
    ex, t = _php_exec("1")
    assert ex.fs_exists("/x") is True
    assert "file_exists(" in t.inner


def test_php_fs_read_bytes_decodes_base64():
    ex, _ = _php_exec(base64.b64encode(b"\x00\x01\x02").decode())
    assert ex.fs_read_bytes("/x") == b"\x00\x01\x02"


def test_php_fs_size_and_mutate():
    ex, _ = _php_exec("42")
    assert ex.fs_size("/x") == 42
    ex2, t2 = _php_exec("OK")
    assert ex2.fs_move("/a", "/b") is True
    assert "rename(" in t2.inner


# -- POSIX command fallback ---------------------------------------------------
def test_command_fs_exists_uses_shell_test():
    ex, t = _cmd_exec("1")
    assert ex.fs_exists("/x") is True
    assert "[ -e /x ]" in t.cmd


def test_command_fs_read_bytes_uses_base64_cmd():
    ex, t = _cmd_exec(base64.b64encode(b"hi").decode())
    assert ex.fs_read_bytes("/etc/hostname") == b"hi"
    assert "base64 /etc/hostname" in t.cmd


def test_command_fs_read_range_uses_tail_head():
    ex, t = _cmd_exec(base64.b64encode(b"abc").decode())
    assert ex.fs_read_range("/x", 10, 3) == b"abc"
    assert "tail -c +11 /x | head -c 3 | base64" in t.cmd


def test_command_fs_write_and_chmod():
    ex, t = _cmd_exec("OK")
    assert ex.fs_write("/tmp/x", b"AB") is True
    assert "base64 -d > /tmp/x" in t.cmd
    ex2, t2 = _cmd_exec("OK")
    assert ex2.fs_chmod("/x", "640") is True
    assert "chmod 640 -- /x" in t2.cmd


def test_command_fs_delete_self_is_unsupported():
    ex, _ = _cmd_exec("OK")
    assert ex.fs_delete(None) is False  # no __FILE__ on a command shell
