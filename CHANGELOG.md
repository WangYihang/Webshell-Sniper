# Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org/).

## [Unreleased] — v2.6 backlog

Completes the prioritized `docs/BACKLOG.md` (v2.6+) on top of the v2.1–v2.5
roadmap.

### Added
- **SOCKS5 pivot** (`socks`): a reGeorg-style local SOCKS5 proxy that relays TCP
  over HTTP through a planted tunnel endpoint (background relay process + on-disk
  spool files), so `curl --socks5`/`proxychains`/a browser can reach
  target-internal hosts. (TUNNEL)
- **Webshell generation** (`--generate PASSWORD`): emit a PHP shell obfuscated
  through the encoder layer (base64/b64var/gzip/xor). (GEN)
- **Evasion**: `b64var` encoder (no `eval(base64_decode(` signature) and
  `--split N` multi-parameter chunked payloads. (ENC+)
- **DB ↔ filesystem**: MySQL `LOAD_FILE`/`INTO DUMPFILE`, PostgreSQL
  `pg_read_file`/`COPY`, and paged full-table CSV export (`db` → `csv`/`rf`/`wf`).
  (DBFS)
- **Output modes** `--output {console,quiet,json}` via a `Renderer` seam. (RENDER)
- **Layered config**: `~/.config/webshell-sniper/config.toml` < `WEBSHELL_SNIPER_*`
  env < CLI flags (`--config`). (CFG)
- **Sessions**: `save`/`hist` commands and `--session FILE` save/restore of
  shells, cwd and history. (SESSION)
- **PTY upgrade** helper (`pty`); post-inject reachability verification;
  per-attempt reverse-shell timeout. (PTY, MISC)

### Changed
- **Metasploit-style UX**: commands now target an **active session** (prompt shows
  `[id]`) instead of always broadcasting; `sessions` lists/switches (`-i`), `-c`
  runs a command on all, `background`/`bg` steps back, and `--all` broadcasts a
  group command. A datastore (`set`/`unset`/`options`, e.g. `LHOST`/`LPORT`/`RANGE`/
  `DB_*`) supplies defaults so pivot/inject stop re-prompting. Meterpreter aliases
  (`sysinfo`, `getuid`, `download`, `upload`, `cat`, `ls`, `ps`, `ifconfig`,
  `netstat`, `getwd`) map onto the namespaced commands. (MSF)
- **Command redesign (UX)**: a unified, namespaced `<group> <action>` vocabulary
  (`recon`/`file`/`pivot`/`inject`) replaces the v1 abbreviations (`p`, `gdf`,
  `fwpf`, `aiw`, `rsh`, ...); session-control verbs (`cd`, `pwd`, `exec`,
  `local`, `remote`, `save`, `history`, `version`, `quit`) stay flat. Every
  command now parses via cmd2 `@with_argparser` — inline flags make the
  previously prompt-only commands (`pivot shell/scan/db`, `inject ...`)
  scriptable, while a TTY still prompts for missing values. (UX)
- **Safety**: bare input now runs on the **target** by default; `!cmd` is always
  local and `exec cmd` always remote. The prompt shows a coloured `REMOTE`/`LOCAL`
  chip plus the tracked cwd so the active machine is never ambiguous. (UX)
- Remote-path `Tab` completion for `cd` and `file ls/read/get/rm` (cached per
  directory); the `db` sub-shell is a real nested cmd2 REPL with its own history,
  `help` and completion. `dla` folded into `file get --find`. (UX)
- Filesystem operations run through language-agnostic `Executor` primitives, so
  file commands also work over command-only shells. (LANG-FS)
- Encoders split into language-neutral byte transforms + per-backend decode
  wrappers; `Transport` formalized behind a `Channel` protocol. (ENC2, CHANNEL)
- Query features (`recon`/`enum`/`portscan`/DB metadata) are pure (return data;
  the REPL renders). (PURE)
- REPL/CLI test coverage raised (gate 60 → 70). (COV)

## [2.0.0] — unreleased

A full modernization. The tool now targets **Python 3.10+** (v1 was Python 2,
EOL since 2020) and ships as an installable package.

### Added
- `pyproject.toml` packaging with [uv](https://docs.astral.sh/uv/); console
  entry points `webshell-sniper` and `webshell-sniper-mount`.
- Configurable HTTP **timeout, proxy, TLS verification and User-Agent**
  (rotating UA pool by default) via CLI flags.
- Automatic command-execution **fallback**: picks the first function not in the
  target's `disable_functions` (`system → passthru → shell_exec → exec → popen
  → proc_open`). v1 detected disabled functions but always called `system()`.
- Per-target failure diagnostics: `WebShell.reason` distinguishes an
  unreachable host from one that responds but does not execute the payload
  (usually a wrong password/parameter) — surfaced by the CLI when a shell is
  rejected.
- File **upload** (`ul` command / `files.upload`) — v1 shipped only an empty
  `upload_file.py` stub.
- `rm` command / self-removal (`unlink(__FILE__)`) for engagement cleanup.
- **Language `Backend` abstraction** (`docs/ARCHITECTURE.md`): PHP specifics
  factored out so the executor is language-agnostic, plus a **command-shell**
  backend and `--lang {php,command}` for non-`eval` shells (e.g. JSP
  `Runtime.exec`), validated against a JSP/Tomcat benchmark target.
- **Plugin system**: third-party REPL command sets discovered via the
  `webshell_sniper.commands` entry-point group (see `docs/plugins.md`).
- **Concurrent** multi-shell operations via `--workers` (batch and the REPL).
- Transport **retry/backoff** on connection errors (read timeouts are not
  retried, to avoid duplicating side effects).
- **PostgreSQL** database backend (PDO) alongside MySQL behind a shared client,
  plus a paginated table `dump`.
- Reverse-shell **methods** (python/perl/php in addition to socat/nc/bash) and
  an optional local listener helper.
- Port-scan **banner grabbing**.
- Pluggable payload **encoders** (`--encoder {base64,gzip,xor}`) that vary the
  on-wire encoding to frustrate static signatures — `xor` randomizes its key
  and decoder variable names every request. Closes v1's unfinished
  "multiple encoders" TODO.
- `--debug` payload/response tracing; command-exec **runtime probe** with
  fallback (handles listed-enabled-but-broken functions); **ranged** large-file
  download; `enum`/`creds` post-exploitation aggregation; a **file manager**
  (`ls`/`mv`/`cp`/`mkdir`/`chmod`/`edit`/`timestomp`).
- Client-tracked remote working directory: `cd`/`pwd` and an interactive
  cwd-aware `shell`.
- File **upload** (`ul`), and rich tables / a download progress bar.
- Non-interactive `--batch {info,exec,inject,download}` mode that runs one
  action across all loaded shells and writes a JSON report — generalises the
  `dev` branch's mass-operation pattern without its scoreboard coupling.
- A full Docker **benchmark** stack (`docker/`): a PHP+Apache target plus a
  seeded MySQL service, with an opt-in `pytest -m benchmark` suite.
- `cmd2`-based REPL with history, `Tab` completion and `help`.
- Test suite (`pytest`): unit tests plus integration tests against a live
  `php -S` target; GitHub Actions CI (Python 3.10–3.13 × PHP 8.3); `ruff`,
  `mypy` and `pre-commit` configuration.
- A disposable Docker test target under `docker/`.
- An explicit authorized-use disclaimer.

### Changed
- Rewrote the 650-line `WebShell` god class into layered modules:
  `core.transport`, `core.executor`, `core.webshell` and a `features/` package.
- Payloads are base64-encoded end to end, eliminating the quote/escaping
  injection bugs in v1's string interpolation.
- MySQL results use ASCII unit/record separators instead of comma-joining, so
  values containing commas no longer corrupt output.
- `rich`-based, markup-safe colored logging.
- Downloads mirror remote paths under `<output-dir>/<host>/` and skip
  unchanged files by MD5.
- Injection generates a random password **per writable directory** by default,
  so discovering one dropped shell does not expose the others; returns
  `(url, password)` pairs.

### Security
- **Download path traversal**: the local save path is built from the target's
  (server-controlled) `find` listing; a malicious/honeypot target could escape
  the output directory via `..`. Such paths are now flattened to a basename.
  Added `SECURITY.md` (authorized-use + reporting policy).

### Fixed
- `mount.py` (now `webshell_sniper.mount`): `rmdir` referenced an undefined
  `mode`; `write` opened files read-only; `random_string` argument order was
  inverted relative to the rest of the codebase.
- Output "compression" that silently never ran (`ob_start('ob_gzip')` — not a
  real PHP callback) was removed.
- Numerous typos in user-facing strings and identifiers (`memery` → `memory`,
  `currect` → `current`, "occured", "Detacting", ...).

### Removed
- Python 2 sources (`webshell-sniper.py`, `core/`, the empty `plugins/` stubs).
- `requirements.txt` listing standard-library modules (`json`, `readline`,
  `urllib`) — dependencies now live in `pyproject.toml`.
