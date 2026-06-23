"""Language backends — everything that is specific to the target's language.

The :class:`~webshell_sniper.core.backends.base.Backend` interface lets the
executor stay language-agnostic; :class:`PHPBackend` is the only implementation
today (see ``docs/ARCHITECTURE.md`` for the plan to add more).
"""

from .base import Backend
from .php import PHPBackend

__all__ = ["Backend", "PHPBackend"]
