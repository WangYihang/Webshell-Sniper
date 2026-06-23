"""Encoders produce well-formed PHP that decodes back to the original payload."""

import base64
import re
import zlib

import pytest

from webshell_sniper.encoders import ENCODERS, get_encoder


def test_base64_round_trip():
    php = "echo 'x';system('id');"
    match = re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", get_encoder("base64")(php))
    assert match
    assert base64.b64decode(match.group(1)).decode() == php


def test_gzip_round_trip():
    php = "echo 'x';" * 50  # compressible
    match = re.fullmatch(
        r"eval\(gzinflate\(base64_decode\('([^']*)'\)\)\);", get_encoder("gzip")(php)
    )
    assert match
    raw = base64.b64decode(match.group(1))
    assert zlib.decompress(raw, -15).decode() == php


def test_xor_round_trip_and_randomized():
    php = "echo 'secret';"
    out1 = get_encoder("xor")(php)
    out2 = get_encoder("xor")(php)
    # Randomized key + variable names => two encodings differ on the wire.
    assert out1 != out2
    # Recover the payload from the emitted PHP and confirm it round-trips.
    blob = re.search(r"base64_decode\('([^']*)'\)", out1).group(1)
    key = re.search(r"='([A-Za-z]{8})';", out1).group(1)
    data = base64.b64decode(blob)
    decoded = bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(data)).decode()
    assert decoded == php


def test_unknown_encoder_raises():
    with pytest.raises(ValueError, match="unknown encoder"):
        get_encoder("rot13")


def test_registry_names():
    assert set(ENCODERS) == {"base64", "gzip", "xor"}
