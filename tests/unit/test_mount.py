"""WebFS (FUSE port) generates valid PHP for each operation (no fuse needed)."""

import base64
import shutil
import subprocess

import pytest

from webshell_sniper.mount import WebFS

php_required = pytest.mark.skipif(shutil.which("php") is None, reason="php not installed")


class FakeExec:
    def __init__(self):
        self.ret = ""
        self.last = ""

    def run_php(self, code: str) -> str:
        self.last = code
        return self.ret


def _lints(code: str) -> bool:
    result = subprocess.run(
        ["php", "-l"], input="<?php " + code + ";", capture_output=True, text=True
    )
    return result.returncode == 0


@php_required
def test_getattr_parses_stat_and_lints():
    fs = WebFS(FakeExec())
    fs.executor.ret = ",".join(str(i) for i in range(13))
    attrs = fs.getattr("/etc/passwd")
    assert attrs["st_mode"] == 2
    assert attrs["st_size"] == 7
    assert _lints(fs.executor.last)


@php_required
def test_read_decodes_base64_and_lints():
    fs = WebFS(FakeExec())
    fs.executor.ret = base64.b64encode(b"hello").decode()
    assert fs.read("/f", 5, 0, None) == b"hello"
    assert _lints(fs.executor.last)


@php_required
def test_write_mkdir_unlink_lint():
    fs = WebFS(FakeExec())
    fs.executor.ret = "5"
    assert fs.write("/f", b"hello", 0, None) == 5
    assert _lints(fs.executor.last)
    fs.executor.ret = "1"
    fs.mkdir("/d", 0o755)
    assert _lints(fs.executor.last)
    fs.unlink("/f")
    assert _lints(fs.executor.last)


def test_readdir_splits_names():
    fs = WebFS(FakeExec())
    fs.executor.ret = "a\nb\nc"
    assert fs.readdir("/d", None) == ["a", "b", "c"]
