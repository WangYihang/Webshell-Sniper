"""Local network helpers."""

from __future__ import annotations

import socket


def get_ip_address() -> str:
    """Best-effort guess of this host's outbound IP.

    Opens a UDP socket towards a public address (no packets are actually
    sent) to discover the routable source IP.  Falls back to loopback when
    the host is offline (e.g. an isolated lab).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()
