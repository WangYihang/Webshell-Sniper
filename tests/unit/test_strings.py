import string

from webshell_sniper.utils.strings import list_to_string, random_string, random_token


def test_random_string_length_and_charset():
    out = random_string(64, "ab")
    assert len(out) == 64
    assert set(out) <= {"a", "b"}


def test_random_string_default_charset_is_letters():
    assert set(random_string(200)) <= set(string.ascii_letters)


def test_random_token_is_quote_safe():
    token = random_token()
    assert "'" not in token and '"' not in token and len(token) == 32


def test_list_to_string():
    assert list_to_string(["a", "b"], "<", ">") == "<a><b>"
