"""Webshell-Sniper — a webshell manager via terminal.

For authorized penetration testing, security research and CTF use only.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("webshell-sniper")
except PackageNotFoundError:  # source checkout without an install
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
