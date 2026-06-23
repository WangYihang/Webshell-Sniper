"""Small string helpers."""

from __future__ import annotations

import secrets
import string


def random_string(length: int, charset: str = string.ascii_letters) -> str:
    """Return a cryptographically-random string of ``length`` chars.

    Unlike the v1 helper (which used :func:`random.choice`) this uses
    :mod:`secrets`, so tokens are not predictable.  The argument order is
    ``(length, charset)`` consistently across the whole package — v1 had two
    conflicting orders (``core`` vs ``mount.py``).
    """
    return "".join(secrets.choice(charset) for _ in range(length))


def random_token(length: int = 32) -> str:
    """Return a random alphabetic sentinel safe to embed in PHP single quotes."""
    return random_string(length, string.ascii_letters)


def list_to_string(items: list[str], prefix: str = "\t[", suffix: str = "]\n") -> str:
    """Render a list as ``prefix<item>suffix`` lines (v1 ``list2string``)."""
    return "".join(f"{prefix}{item}{suffix}" for item in items)
