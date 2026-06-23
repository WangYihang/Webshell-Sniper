"""Runtime configuration shared by the transport and feature layers.

Values are resolved with a clear precedence (highest wins): **CLI flags** over
**environment variables** (``WEBSHELL_SNIPER_*``) over a **config file**
(``~/.config/webshell-sniper/config.toml``) over the built-in defaults. See
:func:`resolve_config`.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any


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
    lang: str = "php"
    split: int = 1  # >1: split the payload across N request params (PHP eval shells)
    retries: int = 2
    retry_backoff: float = 0.5
    workers: int = 1
    debug: bool = False
    output_dir: Path = field(default_factory=lambda: Path.cwd())

    @property
    def proxies(self) -> dict[str, str] | None:
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}


ENV_PREFIX = "WEBSHELL_SNIPER_"

# Only these fields are layerable from env/file (debug/output stay CLI-only).
_LAYERABLE = {
    "timeout", "proxy", "verify_ssl", "user_agent", "encoder", "lang", "split",
    "retries", "retry_backoff", "workers", "output_dir",
}


def default_config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "webshell-sniper" / "config.toml"


def _coerce(name: str, value: Any) -> Any:
    """Coerce a raw (str-ish) value to the dataclass field's type."""
    field_type = {f.name: f.type for f in fields(Config)}[name]
    if isinstance(value, str):
        if "bool" in str(field_type):
            return value.strip().lower() in ("1", "true", "yes", "on")
        if "int" in str(field_type):
            return int(value)
        if "float" in str(field_type):
            return float(value)
        if name == "output_dir":
            return Path(value)
    return value


def _from_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover - needs the tomli backport on 3.10
        import importlib

        try:
            tomllib = importlib.import_module("tomli")
        except ModuleNotFoundError:
            return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return {k: v for k, v in data.items() if k in _LAYERABLE}


def _from_env(env: Mapping[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in _LAYERABLE:
        key = ENV_PREFIX + name.upper()
        if key in env:
            out[name] = env[key]
    return out


def resolve_config(
    cli_overrides: dict[str, Any] | None = None,
    *,
    config_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Config:
    """Build a :class:`Config`, layering file < env < CLI over the defaults."""
    resolved_env: Mapping[str, str] = os.environ if env is None else env
    path = config_path if config_path is not None else default_config_path()

    merged: dict[str, Any] = {}
    merged.update(_from_file(path))
    merged.update(_from_env(resolved_env))
    merged.update({k: v for k, v in (cli_overrides or {}).items() if v is not None})

    coerced = {k: _coerce(k, v) for k, v in merged.items() if k in _LAYERABLE}
    return Config(**coerced)
