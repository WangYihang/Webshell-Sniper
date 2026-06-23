"""The language-backend interface.

A backend owns every fragment of target-language code so the rest of the package
(executor, features) can stay language-agnostic. See ``docs/ARCHITECTURE.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from ...encoders import EncodedPayload

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
    # Byte transforms this backend can decode on the target (see encoders.py).
    # The universal minimum is base64; eval backends add gzip/xor.
    supported_transforms: frozenset[str] = frozenset({"base64"})

    # -- payload decode wrappers ----------------------------------------------
    def wrap_eval(self, payload: EncodedPayload) -> str:
        """Decode ``payload`` and ``eval`` the reconstructed code (eval backends)."""
        raise NotImplementedError(f"{self.name} cannot evaluate code")

    def wrap_command(self, payload: EncodedPayload) -> str:
        """Decode ``payload`` into a shell script and run it (command shells)."""
        raise NotImplementedError(f"{self.name} has no command wrapper")

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

    # -- filesystem primitives -------------------------------------------------
    # Each returns language code that *prints* the result, or ``None`` when the
    # backend cannot express it as evaluated code — the executor then falls back
    # to a POSIX-shell command. This is what lets ``features/files.py`` stay
    # language-agnostic (it asks the executor, never emits a fragment itself).
    #
    # Result-encoding contract (so the executor can parse uniformly):
    #   * boolean ops (write/delete/move/copy/mkdir/chmod) print ``OK``/``FAIL``
    #   * predicate ops (exists/is_dir) print ``1``/``0``
    #   * read_b64/read_range print base64 of the (sub)file's bytes
    #   * list_dir prints rows ``name US size US octal-perm US mtime US type RS``
    #     where US=\x1f, RS=\x1e and type is ``d`` for a directory else ``-``.

    def read_text_code(self, path: str) -> str | None:
        return None

    def read_b64_code(self, path: str) -> str | None:
        return None

    def read_range_code(self, path: str, offset: int, length: int) -> str | None:
        return None

    def size_code(self, path: str) -> str | None:
        return None

    def md5_code(self, path: str) -> str | None:
        return None

    def exists_code(self, path: str) -> str | None:
        return None

    def is_dir_code(self, path: str) -> str | None:
        return None

    def write_code(self, path: str, data_b64: str) -> str | None:
        return None

    def delete_code(self, path: str | None) -> str | None:
        return None

    def list_dir_code(self, path: str) -> str | None:
        return None

    def move_code(self, src: str, dst: str) -> str | None:
        return None

    def copy_code(self, src: str, dst: str) -> str | None:
        return None

    def mkdir_code(self, path: str) -> str | None:
        return None

    def chmod_code(self, path: str, mode: str) -> str | None:
        return None
