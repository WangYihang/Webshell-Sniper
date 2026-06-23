"""Payload encoding, split into two reusable halves (see ``docs/ARCHITECTURE.md``).

A *byte transform* is language-neutral: it turns the payload bytes into a
wire-safe base64 blob (optionally with parameters, e.g. an XOR key). A backend
then supplies the matching *decode wrapper* — the language code that reverses
the transform and runs the result. Splitting them this way means every backend
reuses the same evasion strategies, and a new transform only has to be taught
to each backend's wrapper once.

This replaces v1's single ``Encoder`` callable that emitted PHP directly.
"""

from __future__ import annotations

import base64
import string
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .utils.strings import random_string


@dataclass(frozen=True)
class EncodedPayload:
    """The result of a byte transform: a wire-safe blob plus any parameters."""

    name: str
    b64: str  # base64 of the transformed bytes (always safe on the wire)
    params: dict[str, str] = field(default_factory=dict)


class ByteTransform(ABC):
    """Language-neutral byte-level transform of a payload."""

    name: str = "abstract"

    @abstractmethod
    def apply(self, data: bytes) -> EncodedPayload:
        """Transform ``data`` into a wire-safe :class:`EncodedPayload`."""


class Base64Transform(ByteTransform):
    name = "base64"

    def apply(self, data: bytes) -> EncodedPayload:
        return EncodedPayload(self.name, base64.b64encode(data).decode())


class Base64VarTransform(Base64Transform):
    """Base64 bytes, but the backend decodes via concatenated *variable
    functions* so the literal ``eval(base64_decode(`` signature never appears."""

    name = "b64var"


class GzipTransform(ByteTransform):
    name = "gzip"

    def apply(self, data: bytes) -> EncodedPayload:
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15)  # raw DEFLATE
        raw = compressor.compress(data) + compressor.flush()
        return EncodedPayload("gzip", base64.b64encode(raw).decode())


class XorTransform(ByteTransform):
    name = "xor"

    def apply(self, data: bytes) -> EncodedPayload:
        key = random_string(8, string.ascii_letters)
        xored = bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(data))
        return EncodedPayload("xor", base64.b64encode(xored).decode(), {"key": key})


TRANSFORMS: dict[str, ByteTransform] = {
    "base64": Base64Transform(),
    "b64var": Base64VarTransform(),
    "gzip": GzipTransform(),
    "xor": XorTransform(),
}

# Backwards-friendly alias: the CLI lists encoder *names* from here.
ENCODERS = TRANSFORMS


def get_transform(name: str) -> ByteTransform:
    try:
        return TRANSFORMS[name]
    except KeyError:
        raise ValueError(
            f"unknown encoder: {name!r}; choose from {', '.join(TRANSFORMS)}"
        ) from None
