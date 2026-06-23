# Backlog (v2.6+)

Prioritized backlog of remaining **features** and **improvements**, beyond the
completed v2.1–v2.5 roadmap (see `ROADMAP.md`). Worked top-to-bottom with TDD.

## Working agreement
- **TDD**: write the failing test first (unit with `FakeWS`, or integration
  against the `php -S` fixture / benchmark stack), then implement to green.
- Keep `ruff`, `mypy` and the coverage gate green.
- Commit + push **directly to `main`** per item (no branch / PR). Tick the box
  here in the same commit.

## Legend
Effort **S/M/L**, value **🔴 high / 🟡 medium / 🟢 low**.

---

## P1 — robustness + quick wins + highest-value features
- [x] **DBG** 🔴 S — `--debug` traces the PHP sent and the raw response (stdlib
      `logging`, asserted via `caplog`). → `log.py`, `core/transport.py`,
      `config.py`, `cli.py`
- [x] **PROBE** 🔴 S — probe the chosen command-exec function with a token and
      fall back when it's listed-enabled but silently broken
      (suhosin/open_basedir). → `core/executor.py`
- [x] **CHUNK** 🔴 M — ranged large-file download (filesize + looped
      fseek/fread) to avoid PHP `memory_limit`/POST limits; per-chunk progress.
      → `features/files.py`
- [ ] **ENUM** 🔴 M — aggregate privesc enumeration + credential sweep
      (`sudo -l`, cron, capabilities, world-writable, kernel; read `/etc/passwd`,
      `~/.ssh/`, histories, and auto-extract DB creds from found configs).
      → `features/enum.py`, REPL `enum`
- [ ] **FILEMGR** 🔴 M — file-manager commands: `ls` (table: perms/size/mtime),
      `mv`/`cp`/`mkdir`/`chmod`, in-place `edit`, `timestomp` (`touch -r`).
      → `features/files.py`, REPL

## P2 — capability + DX
- [ ] **CFG** 🟡 S — config file (`~/.config/webshell-sniper/config.toml`) +
      `WEBSHELL_SNIPER_*` env vars layered under CLI flags. → `config.py`, `cli.py`
- [ ] **DBFS** 🟡 M — DB ↔ filesystem (MySQL `LOAD_FILE`/`INTO OUTFILE`, PG
      `COPY`) and full-table export to local CSV. → `features/database.py`
- [ ] **CMDSHELL** 🟡 M — support command-only (non-`eval`) shells, e.g.
      `system($_GET['c'])`; abstract a shell type. → `core/executor.py`, `core/transport.py`, CLI `--shell-type`
- [ ] **ENC+** 🟡 M — more evasion: encoders that avoid the literal
      `eval(base64_decode(` signature (assert/variable-function), and a
      multi-parameter chunked payload. → `encoders.py`, `core/transport.py`
- [ ] **PURE** 🟡 M — separate compute from presentation in `features/*`
      (return structured data; REPL/CLI render). Improves batch/plugin/testing.
      → `features/*`, `repl.py`, `batch.py`

## P3 — bigger / nice-to-have
- [ ] **TUNNEL** 🔴 L — SOCKS5 / port-forward through the shell (reGeorg-style):
      local SOCKS server relays TCP over HTTP via a tunnel PHP endpoint. The
      headline pivot capability. → `features/tunnel.py` + tunnel endpoint
- [ ] **GEN** 🟡 M — generate an initial obfuscated webshell file (reuse
      `encoders`), for planting the first shell. → `features/generate.py`, CLI `generate`
- [ ] **PTY** 🟢 S — reverse-shell PTY upgrade helper (`python -c pty.spawn` +
      `stty` hints). → `features/revshell.py`
- [ ] **COV** 🟢 M — raise REPL/CLI coverage with cmd2's test harness. → `tests/`
- [ ] **MISC** 🟢 S — post-inject reachability verify; per-attempt revshell
      timeout; asciinema demo in README; shell-completion install.

## Non-goals
Multi-language targets (JSP/ASPX/Java) — would require abstracting a language
backend; out of scope. GUI. Windows *target* support (POSIX-focused).
