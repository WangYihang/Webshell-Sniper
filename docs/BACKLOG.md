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
- [x] **ENUM** 🔴 M — aggregate privesc enumeration (`enum`) + credential sweep
      (`creds`): sudo/cron/caps/world-writable/kernel/listening; reads
      passwd/shadow/ssh/histories + greps DB creds from configs.
      → `features/enum.py`, REPL `enum`/`creds`
- [x] **FILEMGR** 🔴 M — file-manager commands: `ls` (table), `mv`/`cp`/`mkdir`/
      `chmod`, in-place `edit` ($EDITOR), `timestomp` (`touch -r`).
      → `features/files.py`, REPL

## P1.5 — Abstraction (see `ARCHITECTURE.md`)
- [x] **LANG** 🔴 M — `Backend` ABC + `PHPBackend` hold every PHP fragment
      (literal/sentinel/exec-builders/disabled-fns/webroot/version); `Executor`,
      `core/php.py` and `core/webshell` route through it. Behaviour-preserving.
      → `core/backends/`
- [x] **LANG-FS** 🔴 M — files/recon expressed via backend FS primitives on the
      `Executor` (`fs_read_text`/`fs_write`/`fs_list`/…); PHP emits eval code,
      command-only shells fall back to POSIX commands. `features/files.py` no
      longer contains a PHP literal. → `core/backends/`, `core/executor.py`,
      `features/files.py`
- [x] **ENC2** 🟡 M — encoders split into language-neutral `ByteTransform`s
      (base64/gzip/xor) + per-backend decode wrappers (`Backend.wrap_eval` /
      `wrap_command`). PHP eval output is byte-identical to before; command-only
      shells now get base64-wrapped (`base64 -d|sh`) evasion too, degrading
      gzip/xor → base64 where unsupported. → `encoders.py`, `core/backends/`
- [x] **LANG-2** 🟡 L — `CommandBackend` (command-only shells) + `--lang
      {php,command}`; validated against the live JSP/Tomcat target. Folds in
      **CMDSHELL**. → `core/backends/command.py`, `core/executor.py`, `cli.py`
- [x] **CHANNEL** 🟡 S — `Channel` protocol (`send(payload)->str`) the executor
      depends on; `Transport` is the HTTP implementation. Non-HTTP channels now
      plug in without touching the executor. → `core/channel.py`, `core/executor.py`
- [x] **RENDER** 🟡 M — `Renderer` (console/quiet/json) behind the `log` facade,
      selected with `--output`; json buffers events and flushes one array.
      Features already return structured data, so this decouples presentation
      without touching call sites. Full per-feature compute/presentation split
      (**PURE**) remains its own item. → `render.py`, `log.py`, `cli.py`
- [x] **SESSION** 🟢 S — `Session` object owns shells/cwd/local_exec/history with
      save/restore; REPL state is session-backed (properties), `save`/`hist`
      commands, and `--session FILE` resumes a snapshot. → `session.py`, `repl.py`, `cli.py`

## P2 — capability + DX
- [x] **CFG** 🟡 S — `resolve_config` layers defaults < `config.toml`
      (`~/.config/webshell-sniper/`, XDG-aware) < `WEBSHELL_SNIPER_*` env <
      CLI flags, with type coercion; `--config` overrides the path. → `config.py`, `cli.py`
- [ ] **DBFS** 🟡 M — DB ↔ filesystem (MySQL `LOAD_FILE`/`INTO OUTFILE`, PG
      `COPY`) and full-table export to local CSV. → `features/database.py`
- [x] **CMDSHELL** 🟡 M — command-only (non-`eval`) shells: done via
      `CommandBackend` + `--lang command` (see LANG-2).
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
