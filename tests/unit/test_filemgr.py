"""File-manager operations: directory listing + mutate ops (no network)."""

from webshell_sniper.features import files

_RS = "\x1e"
_US = "\x1f"


class FakeWS:
    def __init__(self, run_php_ret: str = ""):
        self.run_php_ret = run_php_ret
        self.last_php = ""
        self.last_cmd = ""

    def run_php(self, code: str) -> str:
        self.last_php = code
        return self.run_php_ret

    def run_command(self, command: str) -> str:
        self.last_cmd = command
        return ""


def test_list_dir_parses_entries():
    payload = (
        f"a.txt{_US}100{_US}33188{_US}1700000000{_US}-{_RS}"
        f"sub{_US}4096{_US}16877{_US}1700000001{_US}d{_RS}"
    )
    entries = files.list_dir(FakeWS(payload), "/var/www")
    assert entries[0]["name"] == "a.txt"
    assert entries[0]["size"] == 100
    assert entries[0]["type"] == "-"
    assert entries[0]["mode"] == "rw-r--r--"  # 0o644
    assert entries[1]["type"] == "d"


def test_mutating_ops_generate_expected_php():
    ws = FakeWS("bool(true)")
    assert files.move(ws, "/a", "/b") and "rename(" in ws.last_php
    assert files.copy_file(ws, "/a", "/b") and "copy(" in ws.last_php
    assert files.make_dir(ws, "/d") and "mkdir(" in ws.last_php
    assert files.chmod_path(ws, "/a", "755") and "chmod(" in ws.last_php and "0755" in ws.last_php


def test_timestomp_uses_touch_reference():
    ws = FakeWS()
    files.timestomp(ws, "/a", "/etc/passwd")
    assert "touch -r" in ws.last_cmd
    assert "/etc/passwd" in ws.last_cmd
