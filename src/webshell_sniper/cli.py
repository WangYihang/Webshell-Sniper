"""Command-line entry point: parse args, build webshells, launch the REPL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, batch, encoders, log
from .config import Config
from .core.webshell import WebShell
from .repl import Repl
from .session import Session

EPILOG = """\
examples:
  webshell-sniper http://victim/c.php POST s3cr3t
  webshell-sniper --proxy http://127.0.0.1:8080 http://victim/c.php POST s3cr3t
  webshell-sniper -f webshells.json

Use only against systems you are authorised to test.
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webshell-sniper",
        description="A webshell manager via terminal (authorised pentest / CTF use only).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", nargs="*", help="URL METHOD PASSWORD (or a single .json file)")
    parser.add_argument("-f", "--file", help="load webshells from a JSON file")
    parser.add_argument(
        "--session", help="restore a saved session JSON (shells + cwd) and resume the REPL"
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout (default 15s)")
    parser.add_argument("--proxy", help="proxy URL, e.g. http://127.0.0.1:8080")
    parser.add_argument(
        "--insecure", action="store_true", help="do not verify TLS certificates"
    )
    parser.add_argument("--user-agent", help="fixed User-Agent (default: rotate a small pool)")
    parser.add_argument(
        "--encoder", choices=sorted(encoders.ENCODERS), default="base64",
        help="payload encoding on the wire (default: base64)",
    )
    parser.add_argument(
        "--lang", choices=("php", "command"), default="php",
        help="target shell type: php (eval) or command (e.g. JSP Runtime.exec)",
    )
    parser.add_argument(
        "--batch", choices=batch.ACTIONS,
        help="run an action across all shells non-interactively, write a JSON report, then exit",
    )
    parser.add_argument(
        "--arg", help="argument for --batch (the command for exec, the path for download)"
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="process multiple shells concurrently (default 1 = sequential)",
    )
    parser.add_argument(
        "--output", choices=("console", "quiet", "json"), default="console",
        help="output mode: console (rich), quiet (results+errors only), json",
    )
    parser.add_argument(
        "--debug", action="store_true", help="trace the PHP sent and raw responses"
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path.cwd(),
        help="where downloads and logs are written (default: cwd)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _load_configs(args: argparse.Namespace) -> list[dict[str, str]]:
    """Resolve CLI args into a list of {url, method, password} dicts."""
    json_path = args.file
    if not json_path and len(args.target) == 1 and args.target[0].endswith(".json"):
        json_path = args.target[0]

    if json_path:
        return json.loads(Path(json_path).read_text())
    if len(args.target) == 3:
        url, method, password = args.target
        return [{"url": url, "method": method, "password": password}]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    log.set_renderer(args.output)
    log.set_debug(args.debug)
    try:
        return _run(args, parser)
    finally:
        log.flush()


def _run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    config = Config(
        timeout=args.timeout,
        proxy=args.proxy,
        verify_ssl=not args.insecure,
        user_agent=args.user_agent,
        encoder=args.encoder,
        lang=args.lang,
        workers=args.workers,
        debug=args.debug,
        output_dir=args.output_dir,
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)

    restored: Session | None = None
    if args.session:
        restored = Session.load(args.session, config)
        candidates = restored.shells
        log.info(f"Restoring session from {args.session} ({len(candidates)} shell(s))")
    else:
        configs = _load_configs(args)
        if not configs:
            parser.print_help()
            return 1
        candidates = [
            WebShell(entry["url"], entry["method"], entry["password"], config)
            for entry in configs
        ]

    webshells: list[WebShell] = []
    seen: set[str] = set()
    for ws in candidates:
        log.info(f"Checking {ws} ...")
        if ws.url in seen:
            log.warning("Duplicate URL, skipping.")
            continue
        if ws.connect():
            log.success("Webshell is alive.")
            webshells.append(ws)
            seen.add(ws.url)
        else:
            log.error(f"Webshell unusable: {ws.reason}")

    if not webshells:
        log.error("No working webshells, exiting.")
        return 2

    if args.batch:
        report = batch.run_batch(webshells, args.batch, args.arg, config)
        path = batch.write_report(report, args.batch, config)
        ok = sum(1 for entry in report if entry["ok"])
        log.success(f"Batch '{args.batch}': {ok}/{len(report)} succeeded. Report: {path}")
        return 0 if ok else 2

    log.success(f"{len(webshells)} webshell(s) online. Entering interactive mode.")
    if restored is not None:
        restored.shells = webshells  # keep restored cwd/history, swap in live shells
    return Repl(webshells, config, session=restored).cmdloop() or 0


if __name__ == "__main__":
    sys.exit(main())
