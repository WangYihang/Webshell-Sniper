"""Plugin discovery and concurrent batch execution (no real network)."""

import importlib.metadata
from unittest.mock import MagicMock

import cmd2

from webshell_sniper.batch import run_batch
from webshell_sniper.config import Config
from webshell_sniper.repl import Repl


class _PluginCommands(cmd2.CommandSet):
    def do_plugincmd(self, _):
        """A command contributed by a plugin."""


class _FakeEntryPoint:
    name = "demo"

    def load(self):
        return _PluginCommands


def test_plugin_command_is_registered(monkeypatch):
    def fake_entry_points(group=None):
        return [_FakeEntryPoint()] if group == "webshell_sniper.commands" else []

    monkeypatch.setattr(importlib.metadata, "entry_points", fake_entry_points)
    repl = Repl([MagicMock()], Config())
    assert "plugincmd" in repl.get_all_commands()


class _FakeWS:
    def __init__(self, host: str):
        self.url = f"http://{host}/c.php"
        self.method = "POST"

    def run_command(self, command: str) -> str:
        return f"out:{self.url}"


def test_batch_concurrent_preserves_order():
    shells = [_FakeWS(str(i)) for i in range(6)]
    report = run_batch(shells, "exec", "id", Config(workers=4))
    assert [entry["url"] for entry in report] == [s.url for s in shells]
    assert all(entry["ok"] for entry in report)
