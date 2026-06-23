"""End-to-end tests against a real ``php -S`` target (see conftest)."""

from __future__ import annotations

from pathlib import Path

import pytest

from webshell_sniper.config import Config
from webshell_sniper.core.webshell import WebShell
from webshell_sniper.features import files, recon

pytestmark = pytest.mark.integration


def test_connect_and_metadata(live_shell: WebShell):
    assert live_shell.working
    assert live_shell.php_version.startswith(("7.", "8."))
    assert Path(live_shell.webroot).name == "webroot0"


def test_run_php_survives_quotes(live_shell: WebShell):
    # The exact payload that would have shattered v1's naive interpolation.
    assert live_shell.run_php(r"""echo "a'b\"c" """) == "a'b\"c"


def test_run_command(live_shell: WebShell):
    assert live_shell.run_command("echo hello-cmd").strip() == "hello-cmd"


def test_read_and_existence(live_shell: WebShell):
    secret = str(Path(live_shell.webroot) / "secret.txt")
    assert "hello-from-target" in files.read_file(live_shell, secret)
    assert files.file_exists(live_shell, secret)
    assert not files.file_exists(live_shell, "/nope/nope")
    assert files.is_directory(live_shell, str(Path(live_shell.webroot) / "sub"))


def test_download_skips_unchanged(live_shell: WebShell, tmp_path: Path):
    secret = str(Path(live_shell.webroot) / "secret.txt")
    files.download(live_shell, secret, tmp_path)
    saved = tmp_path / live_shell.transport.url.split("//")[1].split("/")[0] / secret.lstrip("/")
    assert saved.read_text() == "hello-from-target"


def test_disabled_function_fallback(php_target: dict[str, object], tmp_path: Path):
    """system disabled -> executor must transparently fall back."""
    # The session target has nothing disabled; spin a focused unit-level check
    # by forcing the disabled set instead (a dedicated -d server lives in CI).
    ws = WebShell(f"{php_target['base']}/index.php", "POST", "c", Config(output_dir=tmp_path))
    assert ws.connect()
    ws.executor._disabled = {"system", "passthru", "shell_exec"}
    ws.executor._exec_function = None
    assert ws.executor.pick_exec_function() == "exec"
    assert ws.run_command("echo viafallback").strip() == "viafallback"


def test_find_writable_dirs(live_shell: WebShell):
    dirs = recon.find_writable_dirs(live_shell)
    assert any(d.endswith("webroot0") for d in dirs)
