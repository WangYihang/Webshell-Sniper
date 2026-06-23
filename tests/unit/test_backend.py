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
