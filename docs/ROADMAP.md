# Roadmap

Improvement plan for the modernized v2 package. Each milestone is independently
releasable. Legend: effort **S/M/L**, risk **L/M/H**.

## v2.1 — Ergonomics & shell feel
- [ ] Remote `cwd` tracking + interactive `shell` sub-REPL (client-side `cd`,
      commands prefixed `cd <cwd> 2>/dev/null;`) — `core/session.py`, `repl.py`,
      `core/executor.py` — M/L
- [ ] rich tables for `db` results and recon listings — `log.py`,
      `features/database.py`, `features/recon.py` — S/L
- [ ] Download/upload progress bars — `log.py` (rich.progress),
      `features/files.py` — S/L
- [ ] cmd2 command categories + path completion — `repl.py` — S/L

## v2.2 — Evasion & payload encoders
- [ ] Pluggable encoder layer (base64 / gzip+b64 / xor+b64 / random var names /
      chunked), `--encoder` flag — `core/encoders.py`, `core/executor.py`,
      `core/transport.py`, `config.py`, `cli.py` — M/M
- [ ] Request randomization (param/header/UA) — `core/transport.py` — S/L

## v2.3 — Capability
- [ ] DB row dump with pagination + tables — `features/database.py` — S/L
- [ ] PostgreSQL backend (PDO) behind a DB abstraction — `features/database.py` — M/M
- [ ] Reverse-shell methods (python/perl/php) + local `--listener` helper —
      `features/revshell.py` — M/M
- [ ] Port-scan banner grabbing — `features/portscan.py` — S/L

## v2.4 — Architecture & scale
- [ ] Plugin system via entry points + authoring doc — `pyproject.toml`,
      `repl.py`, `docs/plugins.md` — M/M
- [ ] Concurrent multi-shell ops (thread pool) — `repl.py`, `batch.py` — M/M
- [ ] Transport retry/backoff — `core/transport.py` — S/L

## v2.5 — Distribution & assurance
- [ ] PyPI publish workflow + pipx docs — `.github/workflows/`, `README.md` — S/L
- [ ] Raise test coverage (revshell/flag-reaper/memory-inject/mount) + coverage
      gate — `tests/`, `ci.yml` — M/L
- [ ] Security self-review — M/L

## Non-goals
GUI; Windows *target* support (POSIX-focused); the `dev` branch's scoreboard
(Sirius) coupling.
