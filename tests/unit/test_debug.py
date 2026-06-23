"""--debug tracing of the PHP sent and the raw response."""

import logging

import requests

from webshell_sniper import log
from webshell_sniper.config import Config
from webshell_sniper.core.transport import Transport


def _ok_response() -> requests.Response:
    resp = requests.Response()
    resp.status_code = 200
    resp._content = b"BODY-OUT"
    resp.encoding = "utf-8"
    return resp


class FakeSession:
    def request(self, method, url, **kwargs):
        return _ok_response()


def test_debug_traces_payload_and_response(caplog):
    log.set_debug(True)
    try:
        t = Transport("http://x/c.php", "POST", "c", Config(debug=True))
        t._session = FakeSession()
        with caplog.at_level(logging.DEBUG, logger="webshell_sniper"):
            assert t.send("echo 1") == "BODY-OUT"
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "echo 1" in messages       # the PHP we sent
        assert "BODY-OUT" in messages      # the raw response
    finally:
        log.set_debug(False)


def test_debug_off_is_silent(caplog):
    t = Transport("http://x/c.php", "POST", "c", Config())  # debug defaults off
    t._session = FakeSession()
    with caplog.at_level(logging.DEBUG, logger="webshell_sniper"):
        t.send("echo 1")
    assert [r for r in caplog.records if r.levelno == logging.DEBUG] == []
