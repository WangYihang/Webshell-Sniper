"""A :class:`Session` — the mutable state of an interactive engagement.

v1 (and the pre-SESSION REPL) scattered this across ``Repl`` attributes: the
loaded shells, the client-tracked ``cwd``, the local-vs-remote exec toggle and
command history. Bundling them into one serializable object enables save/restore
and scripting: ``q`` (quit) snapshots the session, and ``--session FILE`` rebuilds
it (shells + cwd) on the next run.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Config
from .core.webshell import WebShell


@dataclass
class Session:
    shells: list[WebShell]
    cwd: str = ""  # client-tracked remote working directory
    local_exec: bool = False  # run unrecognised input on the target (vs locally)
    history: list[str] = field(default_factory=list)
    active: int = 0  # index of the session commands target by default (meterpreter-style)
    store: dict[str, str] = field(default_factory=dict)  # datastore: LHOST/LPORT/RANGE/DB_*

    def record(self, command: str) -> None:
        """Append a command to the in-session history (blank lines ignored)."""
        if command.strip():
            self.history.append(command)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cwd": self.cwd,
            "local_exec": self.local_exec,
            "history": self.history,
            "active": self.active,
            "store": self.store,
            "shells": [s.info.to_dict() for s in self.shells],
        }

    def save(self, output_dir: Path) -> Path:
        out = output_dir / f"session_{int(time.time())}.json"
        out.write_text(json.dumps(self.to_dict(), indent=2))
        return out

    @classmethod
    def load(cls, path: str | Path, config: Config) -> Session:
        data = json.loads(Path(path).read_text())
        shells = [
            WebShell(s["url"], s["method"], s["password"], config)
            for s in data.get("shells", [])
        ]
        active = int(data.get("active", 0))
        return cls(
            shells=shells,
            cwd=data.get("cwd", ""),
            local_exec=data.get("local_exec", True),
            history=list(data.get("history", [])),
            active=active if 0 <= active < len(shells) else 0,
            store=dict(data.get("store", {})),
        )
