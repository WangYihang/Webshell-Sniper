"""The language-backend interface.

A backend owns every fragment of target-language code so the rest of the package
(executor, features) can stay language-agnostic. See ``docs/ARCHITECTURE.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

# Given a base64 expression of a command, return code that runs it and prints
# the combined stdout/stderr.
CommandBuilder = Callable[[str], str]


class Backend(ABC):
    name: str = "abstract"
    # Coarse feature flags; features gate language-specific behaviour on these.
    capabilities: frozenset[str] = frozenset()
    # Whether the shell can evaluate arbitrary code in its language (PHP eval).
    # Command-only shells (e.g. a JSP Runtime.exec shell) set this False.
    supports_eval: bool = True

    @abstractmethod
    def literal(self, value: str) -> str:
        """A language expression evaluating to the string ``value`` (quote-safe)."""

    @abstractmethod
    def sentinel(self, token: str, code: str) -> str:
        """Code that prints ``token``, runs ``code``, then prints ``token`` again."""

    @abstractmethod
    def command_builders(self) -> dict[str, CommandBuilder]:
        """Ordered candidate command-exec functions (preferred first)."""

    @abstractmethod
    def disabled_functions_code(self) -> str | None:
        """Code printing the disabled-function list, or None if not applicable."""

    @abstractmethod
    def webroot_code(self) -> str | None:
        """Code printing the document root, or None if not obtainable by eval."""

    @abstractmethod
    def version_code(self) -> str | None:
        """Code printing the runtime version, or None if not obtainable by eval."""
