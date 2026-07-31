"""
Unit tests for the SSRF URL guard (design D7, R1-001).

Deterministic by design: DNS resolution is injected via the module-level
``_resolve_host`` hook, so no test touches the real network.
"""

import socket

import pytest

from app.services.analysis import url_guard
from app.services.analysis.url_guard import validate_external_url


class TestSchemeValidation:
    """Only http/https schemes are allowed (D7)."""

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/file",
            "file:///etc/passwd",
            "ws://example.com/socket",
            "//example.com/path",
            "example.com/path",
        ],
    )
    def test_rejects_non_http_schemes(self, url):
        with pytest.raises(ValueError):
            validate_external_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "https://example.com/products",
            "http://example.com/",
            "http://example.com:8080/path",
        ],
    )
    def test_accepts_http_https_with_public_resolution(self, url, monkeypatch):
        monkeypatch.setattr(url_guard, "_resolve_host", lambda host: ["93.184.216.34"])
        assert validate_external_url(url) == url

    def test_rejects_missing_hostname(self):
        with pytest.raises(ValueError):
            validate_external_url("https:///path-only")


class TestLiteralIpAddresses:
    """Literal IP hosts are checked directly against blocked ranges (D7)."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/admin",  # loopback
            "http://127.0.0.1:8080/",
            "http://10.0.0.5/internal",  # RFC 1918 private
            "http://10.255.255.255/",
            "http://172.16.0.1/",
            "http://172.31.255.255/",  # upper edge of 172.16/12
            "http://192.168.1.10/",
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata
            "http://169.254.0.1/",  # link-local
            "http://100.64.0.1/",  # CGNAT shared address space
            "http://[::1]/",  # IPv6 loopback
            "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
            "http://[fc00::1]/",  # IPv6 unique local
            "http://[fe80::1]/",  # IPv6 link-local
        ],
    )
    def test_rejects_blocked_ranges(self, url):
        with pytest.raises(ValueError):
            validate_external_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://8.8.8.8/",
            "http://93.184.216.34/",
            "http://[2606:2800:220:1:248:1893:25c8:1946]/",
        ],
    )
    def test_accepts_public_literal_ips(self, url):
        assert validate_external_url(url) == url


class TestDnsResolution:
    """Hostname resolution: reject when ANY address lands in a blocked range."""

    def test_accepts_hostname_resolving_to_public(self, monkeypatch):
        monkeypatch.setattr(url_guard, "_resolve_host", lambda host: ["93.184.216.34"])
        assert (
            validate_external_url("https://competidor.com/products")
            == "https://competidor.com/products"
        )

    def test_rejects_hostname_resolving_to_private(self, monkeypatch):
        monkeypatch.setattr(url_guard, "_resolve_host", lambda host: ["10.0.0.5"])
        with pytest.raises(ValueError):
            validate_external_url("http://internal.example.com")

    def test_rejects_when_any_resolved_address_is_private(self, monkeypatch):
        monkeypatch.setattr(
            url_guard, "_resolve_host", lambda host: ["93.184.216.34", "192.168.0.1"]
        )
        with pytest.raises(ValueError):
            validate_external_url("https://mixed.example.com")

    def test_accepts_when_resolution_returns_no_addresses(self, monkeypatch):
        """A hostname that cannot be resolved cannot be fetched: not SSRF.

        Rejecting on transient DNS errors would make the endpoint flaky.
        """

        monkeypatch.setattr(url_guard, "_resolve_host", lambda host: [])
        assert (
            validate_external_url("https://nxdomain.invalid/") == "https://nxdomain.invalid/"
        )

    def test_resolve_host_returns_empty_on_dns_error(self, monkeypatch):
        """The resolver wrapper converts DNS failures into an empty list."""

        def _dns_error(host, port):
            raise OSError("Name or service not known")

        monkeypatch.setattr(socket, "getaddrinfo", _dns_error)
        assert url_guard._resolve_host("nxdomain.invalid") == []

    def test_resolve_host_returns_addresses(self, monkeypatch):
        """The resolver wrapper returns deduplicated A/AAAA records."""

        def _fake_resolver(host, port):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
                (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2606:2800:220:1::1", 0, 0, 0)),
            ]

        monkeypatch.setattr(socket, "getaddrinfo", _fake_resolver)
        assert set(url_guard._resolve_host("example.com")) == {
            "93.184.216.34",
            "2606:2800:220:1::1",
        }


class TestPrivateAddressHelper:
    """Re-check hook used at connection time (DNS rebinding mitigation)."""

    def test_accepts_public_ip(self):
        assert url_guard._is_private_address("93.184.216.34") is False

    def test_rejects_loopback(self):
        assert url_guard._is_private_address("127.0.0.1") is True

    def test_returns_false_for_non_ip(self):
        """Defensive: non-IP input is never treated as a blocked address."""
        assert url_guard._is_private_address("not-an-ip") is False
