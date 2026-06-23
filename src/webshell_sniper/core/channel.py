"""The :class:`Channel` protocol — how a payload reaches the shell.

The executor depends only on this minimal contract, not on HTTP specifically.
:class:`~webshell_sniper.core.transport.Transport` is the default (HTTP)
implementation, but anything with a compatible ``send`` — a raw socket, an
alternate request shape, even a stored-file relay — can be dropped in without
touching the executor or the features above it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Channel(Protocol):
    def send(self, payload: str) -> str:
        """Deliver ``payload`` to the shell and return the raw response body."""
        ...
