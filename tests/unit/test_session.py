"""Session state: history recording + save/restore round-trip."""

import json

from webshell_sniper.config import Config
from webshell_sniper.core.webshell import WebShell
from webshell_sniper.session import Session


def _shell(url="http://t/c.php"):
    return WebShell(url, "POST", "c", Config())


def test_record_skips_blank_lines():
    s = Session([_shell()])
    s.record("id")
    s.record("   ")
    s.record("uname -a")
    assert s.history == ["id", "uname -a"]


def test_save_writes_session_json(tmp_path):
    s = Session([_shell("http://a/c.php")], cwd="/var/www", local_exec=False)
    s.record("whoami")
    out = s.save(tmp_path)
    assert out.exists() and out.name.startswith("session_")
    data = json.loads(out.read_text())
    assert data["cwd"] == "/var/www"
    assert data["local_exec"] is False
    assert data["history"] == ["whoami"]
    assert data["shells"][0]["url"] == "http://a/c.php"


def test_load_round_trips(tmp_path):
    original = Session(
        [_shell("http://a/c.php"), _shell("http://b/c.php")], cwd="/tmp", local_exec=False
    )
    original.record("ls")
    path = original.save(tmp_path)

    restored = Session.load(path, Config())
    assert restored.cwd == "/tmp"
    assert restored.local_exec is False
    assert restored.history == ["ls"]
    assert [s.url for s in restored.shells] == ["http://a/c.php", "http://b/c.php"]


def test_repl_state_is_session_backed():
    from webshell_sniper.repl import Repl

    sess = Session([_shell()], cwd="/srv")
    repl = Repl(sess.shells, Config(), session=sess)
    assert repl.cwd == "/srv"
    repl.cwd = "/opt"
    assert sess.cwd == "/opt"  # property writes through to the session
    repl.local_exec = False
    assert sess.local_exec is False
    assert repl.webshells is sess.shells
