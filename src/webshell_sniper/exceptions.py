"""Exception hierarchy for Webshell-Sniper.

Replaces the bare ``except:`` blocks scattered through the v1 codebase with a
small, explicit hierarchy so callers can distinguish *network* failures from
*payload execution* failures.
"""

from __future__ import annotations


class WebshellError(Exception):
    """Base class for every error raised by this package."""


class ConnectionFailed(WebshellError):
    """The HTTP request to the webshell could not be completed."""


class ExecutionFailed(WebshellError):
    """The payload was delivered but its result could not be recovered.

    Typically this means the token sentinel was not found in the response,
    i.e. the PHP code raised a fatal error or produced no output.
    """


class NoExecFunction(WebshellError):
    """Every known command-execution function is disabled on the target."""
