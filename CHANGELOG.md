# Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org/).

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
