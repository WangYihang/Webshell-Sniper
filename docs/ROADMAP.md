# Roadmap

Improvement plan for the modernized v2 package. Each milestone is independently
releasable. Legend: effort **S/M/L**, risk **L/M/H**.

## v2.1 — Ergonomics & shell feel ✅
- [x] Remote `cwd` tracking + interactive `shell` sub-REPL (client-side `cd`,
      commands prefixed `cd <cwd> 2>/dev/null;`) — `repl.py`
- [x] rich tables for `db` results — `log.py`, `repl.py`
- [x] Download progress bar — `log.py` (rich.progress), `features/files.py`
- [x] cmd2 command categories + local path completion for `ul` — `repl.py`

## v2.2 — Evasion & payload encoders ✅
- [x] Pluggable encoder layer (base64 / gzip / xor with randomized key + var
      names), `--encoder` flag — `encoders.py`, `core/executor.py`,
      `core/webshell.py`, `config.py`, `cli.py`
- [x] Per-request randomization — UA rotation (transport) + per-request xor key
      and decoder variable names

## v2.3 — Capability ✅
- [x] DB row dump with pagination + tables — `features/database.py`
- [x] PostgreSQL backend (PDO) behind a shared `SqlClient` — `features/database.py`
      (live-tested in the benchmark stack)
- [x] Reverse-shell methods (python/perl/php) + local listener helper —
      `features/revshell.py` (bash method live-tested end to end)
- [x] Port-scan banner grabbing — `features/portscan.py` (live-tested)

## v2.4 — Architecture & scale ✅
- [x] Plugin system via entry points + authoring doc — `repl.py`,
      `docs/plugins.md`
- [x] Concurrent multi-shell ops (thread pool, `--workers`) — `repl.py`, `batch.py`
- [x] Transport retry/backoff (connection errors only) — `core/transport.py`

## v2.5 — Distribution & assurance
- [ ] PyPI publish workflow + pipx docs — `.github/workflows/`, `README.md` — S/L
- [ ] Raise test coverage (revshell/flag-reaper/memory-inject/mount) + coverage
      gate — `tests/`, `ci.yml` — M/L
- [ ] Security self-review — M/L

## Non-goals
GUI; Windows *target* support (POSIX-focused); the `dev` branch's scoreboard
(Sirius) coupling.
