"""
Unit Tests for External Verifiers & SSRF Protection
---------------------------------------------------
Tests IP address safety, SSRF blocking, lookalike domain matching, and payment field validation.
"""

import pytest
from app.schemas import ExtractedData
from app.services.verifiers import (
    check_lookalike_domain,
    check_payment_fields,
    check_phone_format,
    check_url_ssrf_safety,
    is_ip_safe,
    levenshtein_distance,
    normalize_homoglyphs,
)


class TestSSRFProtection:
    """Verifies that is_ip_safe and check_url_ssrf_safety block unsafe destinations."""

    @pytest.mark.parametrize(
        "ip,expected_safe",
        [
            ("127.0.0.1", False),
            ("127.0.0.2", False),
            ("::1", False),
            ("10.0.0.1", False),
            ("172.16.0.1", False),
            ("192.168.1.1", False),
            ("169.254.169.254", False),  # AWS / GCP metadata
            ("169.254.1.1", False),      # Link-local
            ("224.0.0.1", False),        # Multicast
            ("8.8.8.8", True),           # Public DNS
            ("1.1.1.1", True),           # Public DNS
            ("142.250.190.46", True),    # Google public IP
        ],
    )
    def test_ip_address_safety_filtering(self, ip: str, expected_safe: bool):
        assert is_ip_safe(ip) == expected_safe

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/admin",
            "http://localhost:8000/metrics",
            "http://169.254.169.254/latest/meta-data/",
            "file:///etc/passwd",
            "gopher://127.0.0.1:6379",
            "ftp://files.example.com",
        ],
    )
    async def test_ssrf_blocks_forbidden_urls(self, url: str):
        is_safe, reason = await check_url_ssrf_safety(url)
        assert is_safe is False
        assert len(reason) > 0


class TestLookalikeDetection:
    """Verifies brand lookalike detection and homoglyph resolution."""

    def test_levenshtein_distance(self):
        assert levenshtein_distance("sbi", "sbi") == 0
        assert levenshtein_distance("sbi", "sbi1") == 1
        assert levenshtein_distance("hdfcbank", "hdfcbannk") == 1
        assert levenshtein_distance("google", "goog1e") == 1

    def test_homoglyph_normalization(self):
        # Cyrillic 'а' normalized to latin 'a'
        assert normalize_homoglyphs("рaytm") == "paytm"
        assert normalize_homoglyphs("sbi0nline") == "sbionline"
        assert normalize_homoglyphs("banrn") == "banm"

    @pytest.mark.asyncio
    async def test_flags_lookalike_spoofing(self):
        results, signals = await check_lookalike_domain("sbi-kyc-update.com")
        assert any(s.id == "LINK_LOOKALIKE_DOMAIN" for s in signals)
        assert any(r.status == "warn" for r in results)

    @pytest.mark.asyncio
    async def test_allows_official_canonical_domain(self):
        results, signals = await check_lookalike_domain("onlinesbi.sbi")
        assert len(signals) == 0
        assert any(r.status == "ok" and "Exact verified match" in r.detail for r in results)

    @pytest.mark.asyncio
    async def test_allows_unrelated_clean_domain(self):
        results, signals = await check_lookalike_domain("example.com")
        assert len(signals) == 0
        assert any(r.status == "ok" for r in results)


class TestPaymentAndPhoneValidators:
    """Tests payment fields and foreign dialling code verifiers."""

    def test_payment_invalid_utr(self):
        text = "Payment received. UTR: 12345 (5 digits only)"
        results, signals = check_payment_fields(text, [])
        assert any(s.id == "PAY_INVALID_UPI_UTR" for s in signals)

    def test_payment_valid_12digit_utr(self):
        text = "Payment received. UPI Ref: 429812984123 (strictly 12 digits)"
        results, signals = check_payment_fields(text, [])
        assert not any(s.id == "PAY_INVALID_UPI_UTR" for s in signals)

    def test_foreign_phone_dialling_code(self):
        phones = ["+923012345678", "+919876543210"]
        results, signals = check_phone_format(phones)
        assert any(s.id == "SENDER_SUSPICIOUS_COUNTRY_CODE" for s in signals)
        assert any("+92" in s.evidence for s in signals)
