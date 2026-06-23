"""SOCKS5 parsing, the HTTP tunnel client, and the endpoint source (no network)."""

import socket
import struct

from webshell_sniper.features import tunnel


class FakeSock:
    """Feeds scripted bytes to recv() and records what was sent."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = bytearray()

    def recv(self, _n):
        return self.chunks.pop(0) if self.chunks else b""

    def sendall(self, data):
        self.sent += data


def test_php_source_has_relay_and_dispatch():
    src = tunnel.tunnel_php_source()
    assert "fsockopen(" in src
    for cmd in ("connect", "write", "read", "close", "relay"):
        assert cmd in src


def test_parse_socks5_ipv4_connect():
    greeting = b"\x05\x01\x00"  # ver, 1 method, no-auth
    request = b"\x05\x01\x00\x01" + socket.inet_aton("10.0.0.5") + struct.pack(">H", 8080)
    sock = FakeSock([greeting[:2], greeting[2:], request[:4], request[4:8], request[8:]])
    assert tunnel._parse_socks5_target(sock) == ("10.0.0.5", 8080)
    assert sock.sent.startswith(b"\x05\x00")  # accepted no-auth


def test_parse_socks5_domain_connect():
    host = b"internal.box"
    request = b"\x05\x01\x00\x03" + bytes([len(host)]) + host + struct.pack(">H", 22)
    sock = FakeSock([b"\x05\x01\x00"[:2], b"\x00", request[:4], bytes([len(host)]), host,
                     struct.pack(">H", 22)])
    assert tunnel._parse_socks5_target(sock) == ("internal.box", 22)


def test_parse_socks5_rejects_non_connect():
    request = b"\x05\x02\x00\x01" + socket.inet_aton("1.1.1.1") + struct.pack(">H", 80)
    sock = FakeSock([b"\x05\x01\x00"[:2], b"\x00", request[:4]])
    assert tunnel._parse_socks5_target(sock) is None


class FakeResp:
    def __init__(self, text="", headers=None, ok=True):
        self.text = text
        self.headers = headers or {}
        self.ok = ok


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, params=None, data=b"", **kw):
        self.calls.append((params, data))
        return self.responses.pop(0)


def test_tunnel_client_connect_write_read_close():
    import base64

    client = tunnel.TunnelClient("http://t/.x.php")
    client._session = FakeSession([
        FakeResp("OK"),                                   # connect
        FakeResp("OK"),                                   # write
        FakeResp(base64.b64encode(b"hi").decode()),       # read -> data
        FakeResp("", headers={"X-Closed": "1"}),          # read -> closed
        FakeResp("OK"),                                   # close
    ])
    sid = client.connect("10.0.0.1", 9000)
    assert sid
    client.write(sid, b"abc")
    assert client._session.calls[1][1] == b"abc"
    assert client.read(sid) == (b"hi", False)
    assert client.read(sid) == (b"", True)
    client.close(sid)
    # connect carries the target host/port
    assert client._session.calls[0][0]["host"] == "10.0.0.1"


def test_tunnel_client_connect_failure_returns_none():
    client = tunnel.TunnelClient("http://t/.x.php")
    client._session = FakeSession([FakeResp("nope", ok=False)])
    assert client.connect("1.2.3.4", 80) is None
