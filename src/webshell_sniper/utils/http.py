"""URL helpers."""

from __future__ import annotations

from urllib.parse import urlsplit


def get_domain(url: str) -> str:
    """Return the ``host[:port]`` portion of a URL.

    >>> get_domain("http://127.0.0.1:8080/c.php")
    '127.0.0.1:8080'
    """
    return urlsplit(url).netloc


def base_url(url: str) -> str:
    """Return ``scheme://host[:port]`` for a URL (no path).

    >>> base_url("http://127.0.0.1/a/b/c.php")
    'http://127.0.0.1'
    """
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"
