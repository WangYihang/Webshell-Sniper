"""REPL command dispatch exercised offline with a fake WebShell."""

import builtins

import pytest

from webshell_sniper.config import Config
from webshell_sniper.repl import Repl
from webshell_sniper.session import Session


class FakeExec:
    def __init__(self):
        self.disabled_functions: set[str] = {"exec"}

    def fs_list(self, path):
        return [("a.txt", 10, "644", 1700000000, "-"), ("d", 4096, "755", 1700000001, "d")]

    def fs_read_text(self, path):
        return f"contents-of-{path}"

    def fs_mkdir(self, path):
        return True

    def fs_chmod(self, path, mode):
        return True

    def fs_move(self, src, dst):
        return True

    def fs_copy(self, src, dst):
        return True


class FakeWS:
    def __init__(self, host="t"):
        from types import SimpleNamespace

        self.url = f"http://{host}/c.php"
        self.method = "POST"
        self.password = "c"
        self.webroot = "/var/www"
        self.php_version = "8.2.0"
        self.kernel_version = "Linux test"
        self.executor = FakeExec()
        self.info = SimpleNamespace(
            to_dict=lambda: {"url": self.url, "method": self.method, "password": "c"}
        )

    def run_command(self, command):
        return f"ran:{command}"

    def run_php(self, code):
        return ""

    def __str__(self):
        return f"{self.method} {self.url}"


@pytest.fixture
def repl():
    return Repl([FakeWS()], Config(output_dir="."), session=Session([FakeWS()]))


def test_info_commands(repl, capsys):
    repl.do_p("")
    repl.do_pv("")
    repl.do_kv("")
    out = capsys.readouterr().out
    assert "8.2.0" in out and "Linux test" in out


def test_pwd_and_exec_toggles(repl, capsys):
    repl.do_setr("")
    assert repl.local_exec is False
    repl.do_setl("")
    assert repl.local_exec is True
    repl.do_pwd("")
    assert "server default" in capsys.readouterr().out


def test_ls_renders_table(repl, capsys):
    repl.do_ls("/var/www")
    out = capsys.readouterr().out
    assert "a.txt" in out and "name" in out


def test_read_and_filemgr_ops(repl, capsys):
    repl.do_r("/etc/passwd")
    repl.do_mkdir("/tmp/x")
    repl.do_chmod("755 /tmp/x")
    repl.do_mv("/a /b")
    repl.do_cp("/a /b")
    out = capsys.readouterr().out
    assert "contents-of-/etc/passwd" in out


def test_chmod_usage_error(repl, capsys):
    repl.do_chmod("onlyone")  # wrong arg count
    assert "usage: chmod" in capsys.readouterr().err  # errors go to stderr


def test_exec_and_remote_default(repl, capsys):
    repl.do_exec("id")
    repl.do_setr("")
    repl.default(_stmt("whoami"))
    out = capsys.readouterr().out
    assert "ran:id" in out and "ran:whoami" in out


def test_history_records_and_lists(repl, capsys):
    repl.do_exec("id")
    repl.do_hist("")
    assert "exec id" in capsys.readouterr().out


def test_pty_command(repl, capsys):
    repl.do_pty("")
    assert "pty.spawn" in capsys.readouterr().out


def test_save_writes_session(tmp_path):
    repl = Repl([FakeWS()], Config(output_dir=tmp_path), session=Session([FakeWS()]))
    repl.do_save("")
    assert list(tmp_path.glob("session_*.json"))


def test_recon_commands_run(repl):
    # These just need to not raise (they call run_command / disabled_functions).
    repl.do_fwd("")
    repl.do_fwpf("")
    repl.do_gdf("")


class _Stmt(str):
    @property
    def raw(self):
        return str(self)


def _stmt(s):
    return _Stmt(s)


def test_local_default_executes(monkeypatch, repl, capsys):
    ran = {}
    monkeypatch.setattr("subprocess.run", lambda *a, **k: ran.setdefault("cmd", a))
    repl.do_setl("")
    repl.default(_stmt("echo hi"))
    assert ran  # local exec path taken


def test_two_arg_usage_error(repl, capsys):
    repl.do_mv("only-one-arg")
    assert "usage: mv" in capsys.readouterr().err


def test_rm_confirm_abort(monkeypatch, repl, capsys):
    monkeypatch.setattr(builtins, "input", lambda *_: "n")
    repl.do_rm("")  # no path -> self-delete -> needs confirmation -> aborted
    assert "Aborted" in capsys.readouterr().out
