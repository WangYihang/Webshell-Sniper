"""File-manager operations: directory listing + mutate ops (no network)."""

from webshell_sniper.features import files


class FakeExecutor:
    """Records FS-primitive calls and returns canned values."""

    def __init__(self, list_rows=None, ok=True):
        self.list_rows = list_rows or []
        self.ok = ok
        self.calls: list[tuple] = []

    def fs_list(self, path):
        self.calls.append(("list", path))
        return self.list_rows

    def fs_move(self, src, dst):
        self.calls.append(("move", src, dst))
        return self.ok

    def fs_copy(self, src, dst):
        self.calls.append(("copy", src, dst))
        return self.ok

    def fs_mkdir(self, path):
        self.calls.append(("mkdir", path))
        return self.ok

    def fs_chmod(self, path, mode):
        self.calls.append(("chmod", path, mode))
        return self.ok


class FakeWS:
    def __init__(self, executor):
        self.executor = executor
        self.last_cmd = ""

    def run_command(self, command: str) -> str:
        self.last_cmd = command
        return ""


def test_list_dir_parses_entries():
    rows = [
        ("a.txt", 100, "644", 1700000000, "-"),
        ("sub", 4096, "755", 1700000001, "d"),
    ]
    entries = files.list_dir(FakeWS(FakeExecutor(list_rows=rows)), "/var/www")
    assert entries[0]["name"] == "a.txt"
    assert entries[0]["size"] == 100
    assert entries[0]["type"] == "-"
    assert entries[0]["mode"] == "rw-r--r--"  # 0o644
    assert entries[1]["type"] == "d"
    assert entries[1]["mode"] == "rwxr-xr-x"  # 0o755


def test_mutating_ops_delegate_to_executor():
    ex = FakeExecutor()
    ws = FakeWS(ex)
    assert files.move(ws, "/a", "/b")
    assert files.copy_file(ws, "/a", "/b")
    assert files.make_dir(ws, "/d")
    assert files.chmod_path(ws, "/a", "755")
    assert ex.calls == [
        ("move", "/a", "/b"),
        ("copy", "/a", "/b"),
        ("mkdir", "/d"),
        ("chmod", "/a", "755"),
    ]


def test_timestomp_uses_touch_reference():
    ws = FakeWS(FakeExecutor())
    files.timestomp(ws, "/a", "/etc/passwd")
    assert "touch -r" in ws.last_cmd
    assert "/etc/passwd" in ws.last_cmd
