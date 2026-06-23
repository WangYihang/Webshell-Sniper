"""Helpers for safely embedding Python values into generated PHP source.

The whole point: never interpolate an attacker-or-operator-supplied string
straight into a PHP single-quoted literal (the v1 approach), because a stray
quote breaks the payload — or worse, lets the *target's* filenames alter your
PHP.  Instead emit ``base64_decode('...')`` so the value is opaque on the wire.
"""

from __future__ import annotations

import base64


def php_string(value: str) -> str:
    """Return a PHP expression that evaluates to ``value`` (a string)."""
    encoded = base64.b64encode(value.encode()).decode()
    return f"base64_decode('{encoded}')"
