"""The language Backend abstraction (PHPBackend holds the PHP-specific bits)."""

import base64
import re

from webshell_sniper.core.backends.base import Backend
from webshell_sniper.core.backends.php import PHPBackend


def test_php_backend_is_a_backend():
    assert isinstance(PHPBackend(), Backend)
    assert PHPBackend().name == "php"


def test_literal_round_trips_and_is_quote_safe():
    match = re.fullmatch(r"base64_decode\('([^']*)'\)", PHPBackend().literal("a'b\"c"))
    assert match
    assert base64.b64decode(match.group(1)).decode() == "a'b\"c"


def test_sentinel_wraps_with_echo():
    assert PHPBackend().sentinel("TOK", "echo 1") == "echo 'TOK';echo 1;echo 'TOK';"


def test_command_builders_order_and_membership():
    builders = PHPBackend().command_builders()
    assert list(builders)[0] == "system"
    assert {"system", "passthru", "shell_exec", "exec", "popen", "proc_open"} <= set(builders)


def test_metadata_and_capabilities():
    backend = PHPBackend()
    assert "phpversion" in backend.version_code()
    assert "DOCUMENT_ROOT" in backend.webroot_code()
    assert "disable_functions" in backend.disabled_functions_code()
    assert {"command", "fs", "mysql"} <= backend.capabilities


def test_php_fs_codegen_uses_expected_functions():
    b = PHPBackend()
    assert "file_get_contents(" in b.read_text_code("/x")
    assert "base64_encode(file_get_contents(" in b.read_b64_code("/x")
    assert b.read_range_code("/x", 5, 10) == (
        "$f=fopen(" + b.literal("/x") + ",'rb');fseek($f,5);"
        "echo base64_encode(fread($f,10));fclose($f)"
    )
    assert "filesize(" in b.size_code("/x")
    assert "md5(" in b.md5_code("/x")
    assert b.exists_code("/x").endswith("?1:0") and "file_exists(" in b.exists_code("/x")
    assert b.is_dir_code("/x").endswith("?1:0") and "is_dir(" in b.is_dir_code("/x")
    assert "file_put_contents(" in b.write_code("/x", "QQ==") and "'OK'" in b.write_code("/x", "QQ==")
    assert "rename(" in b.move_code("/a", "/b")
    assert "copy(" in b.copy_code("/a", "/b")
    assert "mkdir(" in b.mkdir_code("/d")
    assert "chmod(" in b.chmod_code("/a", "755") and "0755" in b.chmod_code("/a", "755")
    assert "scandir(" in b.list_dir_code("/d") and "sprintf('%o'" in b.list_dir_code("/d")


def test_php_delete_self_uses_file_constant():
    assert "__FILE__" in PHPBackend().delete_code(None)
    assert "__FILE__" not in PHPBackend().delete_code("/tmp/x")


def test_php_chmod_rejects_non_octal():
    import pytest

    with pytest.raises(ValueError):
        PHPBackend().chmod_code("/a", "rwx")
