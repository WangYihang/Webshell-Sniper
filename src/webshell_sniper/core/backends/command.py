"""A language-agnostic *command* shell backend.

Models shells that can only run OS commands (no language ``eval``) — e.g. a JSP
``Runtime.exec`` webshell. The parameter value is a ``/bin/sh -c`` script, so
execution and sentinels are expressed in shell, and arbitrary-code execution
(``run_php``) is unavailable. Features that need eval are gated off by the empty
set of language capabilities; command-based features still work.
"""

from __future__ import annotations

from .base import Backend, CommandBuilder


class CommandBackend(Backend):
    name = "command"
    capabilities = frozenset({"command"})
    supports_eval = False

    def literal(self, value: str) -> str:  # not used (no code-gen); raw passthrough
        return value

    def sentinel(self, token: str, code: str) -> str:
        # The shell command is wrapped so its output is bounded by the token.
        return f"echo {token}; {code}; echo {token}"

    def command_builders(self) -> dict[str, CommandBuilder]:
        return {}

    def disabled_functions_code(self) -> str | None:
        return None

    def webroot_code(self) -> str | None:
        return None

    def version_code(self) -> str | None:
        return None
