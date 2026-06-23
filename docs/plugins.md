# Writing plugins

Webshell-Sniper discovers extra REPL commands at startup from the
`webshell_sniper.commands` [entry-point group][ep]. A plugin is just an
installed package that exposes a [`cmd2.CommandSet`][cs] subclass.

## Example

```python
# my_plugin/commands.py
import cmd2


class HelloCommands(cmd2.CommandSet):
    def do_hello(self, _):
        """hello — a command added by a plugin."""
        print("hello from my plugin")
```

Register it in your plugin's `pyproject.toml`:

```toml
[project.entry-points."webshell_sniper.commands"]
hello = "my_plugin.commands:HelloCommands"
```

After `pip install` (or `uv pip install`) of your plugin, the `hello` command
appears in the Webshell-Sniper REPL automatically. A command set that fails to
load is reported as a warning and skipped — it never crashes startup.

## Accessing the session

cmd2 binds the command set to the running `Repl`, so inside a command you can
reach the live state via `self._cmd`:

```python
class ReconCommands(cmd2.CommandSet):
    def do_whoami_all(self, _):
        for ws in self._cmd.webshells:        # the connected WebShell objects
            print(ws.run_command("whoami"))
```

The `WebShell` object exposes `run_php()`, `run_command()` and the
`features/*` helpers operate on it — see the existing `features` modules for
patterns.

[ep]: https://packaging.python.org/en/latest/specifications/entry-points/
[cs]: https://cmd2.readthedocs.io/en/latest/features/modular_commands.html
