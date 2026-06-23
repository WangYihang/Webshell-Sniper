"""Transport retry/backoff semantics (no real network)."""

import pytest
import requests

from webshell_sniper.config import Config
from webshell_sniper.core.transport import Transport
from webshell_sniper.exceptions import ConnectionFailed


def _ok_response() -> requests.Response:
    resp = requests.Response()
    resp.status_code = 200
    resp._content = b"OK"
    resp.encoding = "utf-8"
    return resp


class FlakySession:
    def __init__(self, fail_times: int, exc: Exception):
        self.fail_times = fail_times
        self.exc = exc
        self.calls = 0

    def request(self, method, url, **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        return _ok_response()


def _transport(**cfg):
    t = Transport("http://x/c.php", "POST", "c", Config(retry_backoff=0, **cfg))
    return t


def test_retries_connection_error_then_succeeds():
    t = _transport(retries=2)
    t._session = FlakySession(2, requests.ConnectionError("boom"))
    assert t.send("echo 1") == "OK"
    assert t._session.calls == 3  # 2 failures + 1 success


def test_gives_up_after_configured_retries():
    t = _transport(retries=2)
    t._session = FlakySession(99, requests.ConnectionError("down"))
    with pytest.raises(ConnectionFailed):
        t.send("echo 1")
    assert t._session.calls == 3


def test_read_timeout_is_not_retried():
    # Re-sending could duplicate side effects (e.g. a second reverse shell).
    t = _transport(retries=5)
    t._session = FlakySession(1, requests.ReadTimeout("slow"))
    with pytest.raises(ConnectionFailed):
        t.send("echo 1")
    assert t._session.calls == 1


class CapturingSession:
    def __init__(self):
        self.kwargs = None

    def request(self, method, url, **kwargs):
        self.kwargs = kwargs
        return _ok_response()


def test_multipart_splits_payload_across_params():
    t = _transport(split=3, lang="php")
    t._session = CapturingSession()
    payload = "eval(base64_decode('AAAABBBBCCCC'));"
    t.send(payload)
    data = t._session.kwargs["data"]
    # The eval param now carries only a small re-assembling loader...
    assert data["c"].startswith("eval(") and "$_POST['p0']" in data["c"]
    # ...and the chunks reconstruct the original payload exactly.
    chunks = [data[f"p{i}"] for i in range(3)]
    assert "".join(chunks) == payload
    assert "base64_decode(" not in data["c"]  # signature is split across chunks


def test_multipart_disabled_for_command_backend():
    t = _transport(split=3, lang="command")
    t._session = CapturingSession()
    t.send("echo TOK|base64 -d|sh")
    assert set(t._session.kwargs["data"]) == {"c"}  # single param, no splitting
