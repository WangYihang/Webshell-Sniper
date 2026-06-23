"""Aggregate enumeration + credential sweep orchestration (no network)."""

from webshell_sniper.features import enum


class FakeWS:
    def __init__(self):
        self.commands: list[str] = []

    def run_command(self, command: str) -> str:
        self.commands.append(command)
        return f"OUT[{command[:12]}]"


def test_enumerate_runs_all_checks():
    ws = FakeWS()
    results = enum.enumerate_target(ws)
    assert {
        "whoami", "sudo", "kernel", "cron", "capabilities",
        "world_writable", "suid", "listening", "env",
    } <= set(results)
    joined = " ".join(ws.commands)
    assert "sudo" in joined and "getcap" in joined and "uname" in joined


def test_harvest_reads_cred_files_and_configs():
    ws = FakeWS()
    found = enum.harvest_credentials(ws, ["/var/www/config.php"])
    assert "/etc/passwd" in found
    assert "/var/www/config.php" in found  # DB creds grepped from config
    assert any("grep" in c for c in ws.commands)
    assert any("/etc/passwd" in c for c in ws.commands)
