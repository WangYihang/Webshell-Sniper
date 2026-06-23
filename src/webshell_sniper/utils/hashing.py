"""Hashing helpers used for skip-if-unchanged downloads."""

from __future__ import annotations

import hashlib
from pathlib import Path


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def md5_text(text: str) -> str:
    return md5_bytes(text.encode())


def hash_file(path: str | Path, chunk_size: int = 65536) -> str:
    """Return the MD5 of a local file, streamed so large files are cheap."""
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
