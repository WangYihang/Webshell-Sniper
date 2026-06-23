import base64
import re

from webshell_sniper.core.php import php_string


def test_php_string_is_base64_decode_expr():
    expr = php_string("/etc/passwd")
    match = re.fullmatch(r"base64_decode\('([^']*)'\)", expr)
    assert match
    assert base64.b64decode(match.group(1)).decode() == "/etc/passwd"


def test_php_string_handles_quotes_and_newlines():
    nasty = "a'b\"c\n;system('x')"
    match = re.fullmatch(r"base64_decode\('([^']*)'\)", php_string(nasty))
    # base64 output can't contain a single quote, so the literal is unbreakable,
    # and it must round-trip back to the original (quotes, newline and all).
    assert match
    assert base64.b64decode(match.group(1)).decode() == nasty
