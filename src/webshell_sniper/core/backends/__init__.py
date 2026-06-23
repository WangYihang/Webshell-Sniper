"""Language backends — everything specific to the target's language.

The :class:`Backend` interface lets the executor stay language-agnostic.
:class:`PHPBackend` is an eval shell; :class:`CommandBackend` a command-only
shell (e.g. JSP). See ``docs/ARCHITECTURE.md``.
"""

from .base import Backend
from .command import CommandBackend
from .php import PHPBackend

_BACKENDS: dict[str, type[Backend]] = {"php": PHPBackend, "command": CommandBackend}


def get_backend(name: str) -> Backend:
    try:
        return _BACKENDS[name]()
    except KeyError:
        raise ValueError(
            f"unknown backend: {name!r}; choose from {', '.join(_BACKENDS)}"
        ) from None


__all__ = ["Backend", "CommandBackend", "PHPBackend", "get_backend"]
