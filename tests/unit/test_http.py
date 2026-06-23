import pytest

from webshell_sniper.utils.http import base_url, get_domain


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://127.0.0.1/c.php", "127.0.0.1"),
        ("http://127.0.0.1:8080/a/b.php", "127.0.0.1:8080"),
        ("https://example.com/x", "example.com"),
    ],
)
def test_get_domain(url, expected):
    assert get_domain(url) == expected


def test_base_url_strips_path():
    assert base_url("http://127.0.0.1/a/b/c.php") == "http://127.0.0.1"
    assert base_url("https://h:8443/x") == "https://h:8443"
