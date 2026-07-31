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

Resolution failures (NXDOMAIN, transient DNS errors) are accepted: a
hostname that cannot be resolved cannot be fetched, so it poses no SSRF
risk, and rejecting it here would make the endpoint flaky.
"""

import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

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
    """Resolve a hostname to its A/AAAA records (empty list on failure)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return []
    return list({info[4][0] for info in infos})


def validate_external_url(url: str) -> str:
    """Validate that ``url`` is a public http/https URL.

    Raises ValueError with a human-readable reason when the URL targets a
    blocked scheme, a blocked literal IP range, or a hostname that resolves
    to a blocked range. The API layer maps ValueError to HTTP 400.

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
    for address in _resolve_host(host):
        if _is_private_address(address):
            raise ValueError(
                f"URL host '{host}' resolves to a blocked private/loopback address"
            )
    return url
