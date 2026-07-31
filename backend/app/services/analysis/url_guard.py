"""
SSRF guard for URLs accepted by the analysis API (design D7, R1-001).

Rejects URLs that could target internal infrastructure:

- Only ``http``/``https`` schemes are allowed.
- Literal IP hosts are checked directly against private/loopback/link-local/
  metadata ranges.
- DNS hostnames are resolved and rejected when ANY resolved address falls in
  one of those ranges (169.254.169.254, ::1, 127.0.0.0/8, 10/8, 172.16/12,
  192.168/16, 100.64/10, IPv6 ULA/link-local).

DNS REBINDING MITIGATION: this guard validates the URL at input time only.
Code that later opens a connection MUST re-resolve the hostname and re-check
the address (see ``_is_private_address``) right before connecting; otherwise
a hostname that resolves publicly at validation time could be rebound to an
internal address by the time the connection opens.

Resolution failures (OSError) and timeouts fail closed with ValueError: a
hostname that cannot be resolved within the timeout is not a usable public
target, and failing the guard keeps the API responsive when the resolver is
slow or black-holed. Resolution itself runs off the event loop (worker
thread) under a timeout, so a stalled resolver can never block the loop.
"""

import asyncio
import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

# How long a single hostname resolution may take before the guard fails
# closed. Keeps a stalled/black-holed resolver from blocking the API.
RESOLVE_TIMEOUT_SECONDS = 5.0

# Blocked ranges per design D7, plus IPv6 ULA/link-local for parity.
_PRIVATE_NETWORKS: List[ipaddress._BaseNetwork] = [
    ipaddress.ip_network("127.0.0.0/8"),  # loopback (incl. 127.0.0.1)
    ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 private
    ipaddress.ip_network("169.254.0.0/16"),  # link-local (incl. 169.254.169.254 metadata)
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT shared address space
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


def _is_private_address(address: str) -> bool:
    """True if the IP address falls in a blocked private/loopback range."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    # IPv4-mapped IPv6 addresses (::ffff:a.b.c.d) must be checked as IPv4.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return any(ip in network for network in _PRIVATE_NETWORKS)


def _resolve_host(host: str) -> List[str]:
    """Resolve a hostname to its A/AAAA records.

    Raises OSError when the name cannot be resolved (NXDOMAIN, resolver
    failure). Runs in a worker thread via ``asyncio.to_thread`` — never on
    the event loop.
    """
    infos = socket.getaddrinfo(host, None)
    return list({info[4][0] for info in infos})


async def _resolve_host_with_timeout(host: str) -> List[str]:
    """Resolve ``host`` off the event loop, bounded by the resolve timeout.

    Raises ValueError when resolution fails (OSError) or exceeds
    ``RESOLVE_TIMEOUT_SECONDS``, so a stalled resolver fails the guard
    instead of blocking the event loop.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_resolve_host, host),
            timeout=RESOLVE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise ValueError(
            f"Timed out resolving host '{host}' after {RESOLVE_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise ValueError(f"Could not resolve host '{host}': {exc}") from exc


async def validate_external_url(url: str) -> str:
    """Validate that ``url`` is a public http/https URL.

    Coroutine: the DNS resolution step runs in a worker thread with a
    timeout, so a slow or hung resolver cannot block the event loop.

    Raises ValueError with a human-readable reason when the URL targets a
    blocked scheme, a blocked literal IP range, or a hostname that resolves
    to a blocked range (or cannot be resolved within the timeout). The API
    layer maps ValueError to HTTP 400.

    Returns the URL unchanged when valid.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")
    host = parsed.hostname
    if not host:
        raise ValueError("URL must include a hostname")

    # Literal IP hosts are checked directly; no DNS involved.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if _is_private_address(host):
            raise ValueError(
                f"URL host '{host}' resolves to a blocked private/loopback address"
            )
        return url

    # DNS hostname: reject when ANY resolved address is blocked.
    for address in await _resolve_host_with_timeout(host):
        if _is_private_address(address):
            raise ValueError(
                f"URL host '{host}' resolves to a blocked private/loopback address"
            )
    return url
