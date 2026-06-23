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
