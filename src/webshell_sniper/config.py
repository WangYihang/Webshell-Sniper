"""Runtime configuration shared by the transport and feature layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Tunable settings for talking to a webshell.

    Everything that was hard-coded in v1 (the ``timeout=5``, the implicit
    proxy-via-proxychains, the lack of TLS control) is configurable here.
    """

    timeout: float = 15.0
    proxy: str | None = None
    verify_ssl: bool = True
    user_agent: str | None = None
    encoder: str = "base64"
    retries: int = 2
    retry_backoff: float = 0.5
    workers: int = 1
    output_dir: Path = field(default_factory=lambda: Path.cwd())

    @property
    def proxies(self) -> dict[str, str] | None:
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}
