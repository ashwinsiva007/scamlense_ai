"""
Verifiers Service
-----------------
Performs external domain, URL reputation, and identity checks using threat intelligence APIs.
Includes strict SSRF protection, brand lookalike detection, domain age verification,
URL unshortening, and UPI/phone formatting checks.
"""

import asyncio
from datetime import datetime, timezone
import ipaddress
import logging
import os
import re
import socket
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.parse

import httpx
import yaml

from app.config import settings
from app.schemas import ExtractedData, Signal, ToolResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# In-Memory Cache (1-hour TTL)
# ------------------------------------------------------------------------------
_CACHE_TTL_SECONDS = 3600
_LOOKUP_CACHE: Dict[str, Tuple[float, Any]] = {}

def _get_from_cache(key: str) -> Optional[Any]:
    if key in _LOOKUP_CACHE:
        timestamp, value = _LOOKUP_CACHE[key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            return value
        del _LOOKUP_CACHE[key]
    return None

def _put_to_cache(key: str, value: Any) -> None:
    _LOOKUP_CACHE[key] = (time.time(), value)


# ------------------------------------------------------------------------------
# SSRF Protection
# ------------------------------------------------------------------------------
_METADATA_IPS = {"169.254.169.254", "metadata.google.internal"}

def is_ip_safe(ip_str: str) -> bool:
    """
    Validates whether an IP address is safe for outbound server queries.
    Rejects loopback, private, link-local, multicast, reserved, and cloud metadata IPs.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback:
            return False
        if ip.is_private:
            return False
        if ip.is_link_local:
            return False
        if ip.is_multicast:
            return False
        if ip.is_reserved:
            return False
        if str(ip) in _METADATA_IPS:
            return False
        # Specific check for IPv4 mapped IPv6 addresses
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return is_ip_safe(str(ip.ipv4_mapped))
        return True
    except ValueError:
        return False


async def check_url_ssrf_safety(url: str) -> Tuple[bool, str]:
    """
    Verifies URL scheme and resolves hostname via DNS.
    Returns (True, hostname) if safe, or (False, reason) if blocked.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme '{parsed.scheme}'"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        if hostname.lower() in _METADATA_IPS or hostname.lower() == "localhost":
            return False, f"Blocked forbidden hostname: {hostname}"

        # Resolve hostname asynchronously
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            return False, f"DNS resolution failed for {hostname}"

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            if not is_ip_safe(ip_str):
                return False, f"Host {hostname} resolved to forbidden IP {ip_str}"

        return True, hostname
    except Exception as e:
        return False, f"URL parse/validation error: {e}"


# ------------------------------------------------------------------------------
# Levenshtein & Homoglyph Helpers for Lookalike Detection
# ------------------------------------------------------------------------------
_HOMOGLYPH_MAP = {
    # Cyrillic to Latin
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ԛ": "q", "ԝ": "w",
    # Common digit/char confusions
    "0": "o", "1": "l", "5": "s", "8": "b",
}

def normalize_homoglyphs(text: str) -> str:
    res = []
    # multi-char replacement first
    normalized = text.lower().replace("rn", "m").replace("vv", "w")
    for char in normalized:
        res.append(_HOMOGLYPH_MAP.get(char, char))
    return "".join(res)

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


# ------------------------------------------------------------------------------
# Brands Database Loader
# ------------------------------------------------------------------------------
_BRANDS_DATA: Optional[List[Dict[str, Any]]] = None

def get_brands() -> List[Dict[str, Any]]:
    global _BRANDS_DATA
    if _BRANDS_DATA is None:
        data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "brands.yaml")
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    _BRANDS_DATA = content.get("brands", [])
            except Exception as e:
                logger.error(f"Failed to load brands.yaml: {e}")
                _BRANDS_DATA = []
        else:
            _BRANDS_DATA = []
    return _BRANDS_DATA


# ------------------------------------------------------------------------------
# Verifier Implementations
# ------------------------------------------------------------------------------

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "rb.gy", "t.co",
    "t.ly", "rebrand.ly", "shorturl.at", "tiny.cc", "ow.ly", "buff.ly",
}

async def unshorten_url(url: str) -> Tuple[str, List[ToolResult], List[Signal]]:
    """
    Follows HTTP redirects up to 5 hops with SSRF checks on each hop.
    Limits response body read to 64KB.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []
    current_url = url
    hops = 0
    max_hops = 5

    try:
        parsed_init = urllib.parse.urlparse(url)
        domain = (parsed_init.hostname or "").lower()
        is_known_shortener = domain in SHORTENER_DOMAINS

        if is_known_shortener:
            signals.append(
                Signal(
                    id="LINK_SHORTENED_URL",
                    label="Obfuscated or Shortened URL",
                    category="links",
                    weight=10.0,
                    evidence=url,
                    source="tool",
                )
            )

        async with httpx.AsyncClient(timeout=3.5, follow_redirects=False) as client:
            while hops < max_hops:
                safe, reason = await check_url_ssrf_safety(current_url)
                if not safe:
                    is_dns_failure = "DNS resolution failed" in reason
                    results.append(
                        ToolResult(
                            tool="unshorten",
                            target=current_url,
                            status="skipped" if is_dns_failure else "error",
                            detail=reason if is_dns_failure else f"SSRF safety check blocked request: {reason}",
                        )
                    )
                    return current_url, results, signals

                try:
                    # Limit response body reading to max 64KB
                    async with client.stream("GET", current_url, headers={"User-Agent": "ScamLens-Verifier/1.0"}) as resp:
                        read_bytes = 0
                        async for chunk in resp.aiter_bytes():
                            read_bytes += len(chunk)
                            if read_bytes >= 65536:
                                break
                        is_redirect = resp.is_redirect and "location" in resp.headers
                        location_header = resp.headers.get("location")
                except Exception as req_err:
                    results.append(
                        ToolResult(
                            tool="unshorten",
                            target=current_url,
                            status="warn" if is_known_shortener else "skipped",
                            detail=f"Network resolution error: {req_err}",
                        )
                    )
                    return current_url, results, signals

                if is_redirect and location_header:
                    next_url = urllib.parse.urljoin(current_url, location_header)
                    current_url = next_url
                    hops += 1
                else:
                    break

        status = "warn" if hops > 0 or is_known_shortener else "ok"
        detail = f"Expanded to {current_url} after {hops} hops" if hops > 0 else "Direct URL"
        results.append(
            ToolResult(
                tool="unshorten",
                target=url,
                status=status,
                detail=detail,
            )
        )
    except Exception as e:
        results.append(
            ToolResult(
                tool="unshorten",
                target=url,
                status="error",
                detail=f"Unshortener failed: {e}",
            )
        )

    return current_url, results, signals


async def check_lookalike_domain(domain: str) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Checks if domain mimics a legitimate brand from brands.yaml:
    - Levenshtein distance <= 2 to canonical domains
    - Homoglyph / character substitutions
    - Brand name as subdomain/slug of an unrelated domain
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    domain_clean = domain.lower().strip()
    if not domain_clean or "." not in domain_clean:
        return results, signals

    bare_domain = domain_clean[4:] if domain_clean.startswith("www.") else domain_clean

    brands = get_brands()
    norm_domain = normalize_homoglyphs(domain_clean)

    # Check for exact matches first
    for brand in brands:
        canonical = [cd.lower().strip() for cd in brand.get("canonical_domains", [])]
        if domain_clean in canonical or bare_domain in canonical:
            results.append(
                ToolResult(
                    tool="lookalike",
                    target=domain_clean,
                    status="ok",
                    detail=f"Exact verified match for official {brand['name']} domain",
                )
            )
            signals.append(
                Signal(
                    id="REDUCER_VERIFIED_BRAND_DOMAIN",
                    label="Exact Verified Brand Domain Match",
                    category="reducers",
                    weight=-15.0,
                    evidence=bare_domain,
                    source="tool",
                )
            )
            return results, signals

    # Check for lookalike spoofing
    for brand in brands:
        brand_name = brand["name"]
        keywords = [k.lower().strip() for k in brand.get("keywords", [])]
        canonicals = [cd.lower().strip() for cd in brand.get("canonical_domains", [])]

        for cdom in canonicals:
            cdom_base = cdom.split(".")[0]
            dom_base = domain_clean.split(".")[0]

            # 1. Levenshtein edit distance <= 2 on domain base or full domain
            dist_base = levenshtein_distance(dom_base, cdom_base)
            dist_full = levenshtein_distance(domain_clean, cdom)

            is_lookalike = False
            reason = ""

            if dist_base <= 2 and len(dom_base) >= 4 and dom_base != cdom_base:
                is_lookalike = True
                reason = f"Domain base '{dom_base}' is suspiciously similar to official '{cdom_base}' (edit distance {dist_base})"
            elif dist_full <= 2 and domain_clean != cdom:
                is_lookalike = True
                reason = f"Domain '{domain_clean}' is suspiciously similar to official '{cdom}' (edit distance {dist_full})"

            # 2. Homoglyph normalized match
            norm_cdom = normalize_homoglyphs(cdom)
            if not is_lookalike and norm_domain == norm_cdom and domain_clean != cdom:
                is_lookalike = True
                reason = f"Domain uses homoglyph character substitutions to mimic '{cdom}'"

            # 3. Brand keyword present as subdomain or slug in an unrelated domain
            if not is_lookalike:
                for kw in keywords:
                    if len(kw) >= 3 and kw in domain_clean and not any(domain_clean.endswith("." + cd) or domain_clean == cd for cd in canonicals):
                        is_lookalike = True
                        reason = f"Brand name '{kw}' used in unrelated external domain '{domain_clean}'"
                        break

            if is_lookalike:
                signals.append(
                    Signal(
                        id="LINK_LOOKALIKE_DOMAIN",
                        label="Spoofed or Lookalike Brand Domain",
                        category="links",
                        weight=25.0,
                        evidence=f"{domain_clean} (mimics {brand_name})",
                        source="tool",
                    )
                )
                results.append(
                    ToolResult(
                        tool="lookalike",
                        target=domain_clean,
                        status="warn",
                        detail=reason,
                    )
                )
                return results, signals

    # Clean domain
    results.append(
        ToolResult(
            tool="lookalike",
            target=domain_clean,
            status="ok",
            detail="No brand typosquatting or lookalike patterns identified",
        )
    )
    return results, signals


async def check_domain_age(domain: str) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Queries RDAP via https://rdap.org/domain/{domain} with 3s timeout.
    Flags domains registered < 90 days ago.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    domain_clean = domain.lower().strip()
    cache_key = f"rdap_{domain_clean}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    url = f"https://rdap.org/domain/{domain_clean}"
    safe, reason = await check_url_ssrf_safety(url)
    if not safe:
        res = ([ToolResult(tool="domain_age", target=domain_clean, status="skipped", detail=f"SSRF blocked: {reason}")], [])
        _put_to_cache(cache_key, res)
        return res

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, headers={"Accept": "application/rdap+json", "User-Agent": "ScamLens-Verifier/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                reg_date = None
                for ev in events:
                    if ev.get("eventAction") in ("registration", "created"):
                        reg_date_str = ev.get("eventDate")
                        if reg_date_str:
                            try:
                                # Parse ISO date
                                reg_date = datetime.fromisoformat(reg_date_str.replace("Z", "+00:00"))
                            except Exception:
                                pass
                            break

                if reg_date:
                    age_days = (datetime.now(timezone.utc) - reg_date).days
                    if age_days < 90:
                        signals.append(
                            Signal(
                                id="LINK_YOUNG_DOMAIN",
                                label="Newly Registered Domain (<90 Days Old)",
                                category="links",
                                weight=15.0,
                                evidence=f"{domain_clean} (registered {age_days} days ago)",
                                source="tool",
                            )
                        )
                        results.append(
                            ToolResult(
                                tool="domain_age",
                                target=domain_clean,
                                status="warn",
                                detail=f"Domain registered {age_days} days ago (< 90 days threshold)",
                            )
                        )
                    else:
                        results.append(
                            ToolResult(
                                tool="domain_age",
                                target=domain_clean,
                                status="ok",
                                detail=f"Domain registered {age_days} days ago",
                            )
                        )
                    res = (results, signals)
                    _put_to_cache(cache_key, res)
                    return res

        results.append(
            ToolResult(
                tool="domain_age",
                target=domain_clean,
                status="skipped",
                detail="RDAP registration date not found or query timed out",
            )
        )
    except Exception as e:
        results.append(
            ToolResult(
                tool="domain_age",
                target=domain_clean,
                status="skipped",
                detail=f"RDAP lookup failed: {e}",
            )
        )

    res = (results, signals)
    _put_to_cache(cache_key, res)
    return res


async def check_safe_browsing(url: str) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Queries Google Safe Browsing Lookup API (v4) if SAFE_BROWSING_KEY is set.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    key = settings.SAFE_BROWSING_KEY
    if not key:
        return [ToolResult(tool="safe_browsing", target=url, status="skipped", detail="API key not configured")], []

    cache_key = f"gsb_{url}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"
    payload = {
        "client": {"clientId": "scamlens", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.post(endpoint, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matches", [])
                if matches:
                    threat_type = matches[0].get("threatType", "MALICIOUS")
                    signals.append(
                        Signal(
                            id="LINK_THREAT_FEED_MATCH",
                            label="Domain Flagged on Security Threat Feeds",
                            category="links",
                            weight=40.0,
                            evidence=f"{url} ({threat_type})",
                            source="tool",
                        )
                    )
                    results.append(
                        ToolResult(
                            tool="safe_browsing",
                            target=url,
                            status="error",
                            detail=f"URL flagged as {threat_type} by Google Safe Browsing",
                        )
                    )
                else:
                    results.append(
                        ToolResult(
                            tool="safe_browsing",
                            target=url,
                            status="ok",
                            detail="No threat matches in Google Safe Browsing feed",
                        )
                    )
            else:
                results.append(
                    ToolResult(
                        tool="safe_browsing",
                        target=url,
                        status="skipped",
                        detail=f"Safe Browsing API returned HTTP {resp.status_code}",
                    )
                )
    except Exception as e:
        results.append(
            ToolResult(
                tool="safe_browsing",
                target=url,
                status="skipped",
                detail=f"Safe Browsing check failed: {e}",
            )
        )

    res = (results, signals)
    _put_to_cache(cache_key, res)
    return res


async def check_urlhaus(url: str) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Queries abuse.ch URLhaus API for active malware/phishing reports.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    key = settings.URLHAUS_KEY
    if not key:
        return [ToolResult(tool="urlhaus", target=url, status="skipped", detail="URLhaus API key not configured (URLHAUS_KEY)")], []

    cache_key = f"urlhaus_{url}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    endpoint = "https://urlhaus-api.abuse.ch/v1/url/"
    headers = {"User-Agent": "ScamLens-Verifier/1.0", "Auth-Key": key}

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.post(endpoint, data={"url": url}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                query_status = data.get("query_status")
                if query_status == "ok":
                    url_status = data.get("url_status", "active")
                    threat = data.get("threat", "malware_download")
                    signals.append(
                        Signal(
                            id="LINK_THREAT_FEED_MATCH",
                            label="Domain Flagged on Security Threat Feeds",
                            category="links",
                            weight=40.0,
                            evidence=f"{url} ({threat})",
                            source="tool",
                        )
                    )
                    results.append(
                        ToolResult(
                            tool="urlhaus",
                            target=url,
                            status="error",
                            detail=f"URL listed on URLhaus (threat: {threat}, status: {url_status})",
                        )
                    )
                else:
                    results.append(
                        ToolResult(
                            tool="urlhaus",
                            target=url,
                            status="ok",
                            detail="Not found in URLhaus active threat dataset",
                        )
                    )
            else:
                results.append(
                    ToolResult(
                        tool="urlhaus",
                        target=url,
                        status="skipped",
                        detail=f"URLhaus returned HTTP {resp.status_code}",
                    )
                )
    except Exception as e:
        results.append(
            ToolResult(
                tool="urlhaus",
                target=url,
                status="skipped",
                detail=f"URLhaus check failed: {e}",
            )
        )

    res = (results, signals)
    _put_to_cache(cache_key, res)
    return res


def check_free_webmail(sender: Optional[str], text: str, claimed_brand: Optional[str]) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Checks if sender uses free public webmail while claiming official or corporate identity.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    if not sender:
        return results, signals

    sender_clean = sender.lower().strip()
    free_domains = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@rediffmail.com", "@live.com")
    is_free_mail = any(sender_clean.endswith(fd) or fd in sender_clean for fd in free_domains)

    if not is_free_mail:
        return results, signals

    official_keywords = (
        "bank", "hr", "recruitment", "careers", "official", "support",
        "tax", "customs", "police", "kyc", "sbi", "hdfc", "icici", "amazon"
    )

    combined_context = f"{text} {claimed_brand or ''}".lower()
    claims_official = any(kw in combined_context for kw in official_keywords)

    if claims_official:
        signals.append(
            Signal(
                id="SENDER_FREE_WEBMAIL_OFFICIAL",
                label="Free Webmail Used for Corporate or Official Entity",
                category="sender",
                weight=15.0,
                evidence=sender,
                source="tool",
            )
        )
        results.append(
            ToolResult(
                tool="free_mail_check",
                target=sender,
                status="warn",
                detail="Official or corporate entity communicating via free public webmail",
            )
        )
    else:
        results.append(
            ToolResult(
                tool="free_mail_check",
                target=sender,
                status="ok",
                detail="Free webmail detected without corporate impersonation claims",
            )
        )

    return results, signals


def check_phone_format(phones: List[str]) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Checks phone numbers for Indian mobile formatting vs suspicious foreign dialling codes.
    States clearly what it can and cannot verify (format only; cannot verify subscriber identity).
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    suspicious_codes = [
        ("+92", "Pakistan"),
        ("+84", "Vietnam"),
        ("+234", "Nigeria"),
        ("+254", "Kenya"),
        ("+62", "Indonesia"),
        ("+63", "Philippines"),
    ]

    for phone in phones:
        clean = phone.strip()
        matched_suspicious = False
        for prefix, country in suspicious_codes:
            if clean.startswith(prefix):
                signals.append(
                    Signal(
                        id="SENDER_SUSPICIOUS_COUNTRY_CODE",
                        label="Suspicious Foreign Country Code",
                        category="sender",
                        weight=15.0,
                        evidence=clean,
                        source="tool",
                    )
                )
                results.append(
                    ToolResult(
                        tool="phone_check",
                        target=clean,
                        status="warn",
                        detail=f"Originates from {country} ({prefix}), commonly abused in cross-border fraud targeting India. Note: Format check only; cannot verify true subscriber.",
                    )
                )
                matched_suspicious = True
                break

        if not matched_suspicious:
            # Check for standard Indian mobile number (+91 or 10-digit starting with 6,7,8,9)
            is_indian_mobile = bool(re.match(r"^(?:\+91[\s-]?)?[6-9]\d{9}$", clean.replace(" ", "").replace("-", "")))
            if is_indian_mobile:
                results.append(
                    ToolResult(
                        tool="phone_check",
                        target=clean,
                        status="ok",
                        detail="Standard Indian mobile number format. Note: Format verification only; does not authenticate caller identity.",
                    )
                )
            else:
                results.append(
                    ToolResult(
                        tool="phone_check",
                        target=clean,
                        status="ok",
                        detail="Phone format parsed. Note: Format check only; cannot authenticate caller identity.",
                    )
                )

    return results, signals


def check_upi_format(upi_ids: List[str]) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Validates UPI VPAs against standard bank PSP patterns.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    valid_psp_handles = {
        "okaxis", "okhdfcbank", "oksbi", "okicici", "paytm", "ybl", "ibl",
        "axl", "barodampay", "apl", "idfcbank", "fbl", "postbank", "federal"
    }

    for upi in upi_ids:
        clean = upi.strip().lower()
        if "@" in clean:
            user_part, psp_part = clean.split("@", 1)
            # Suspicious if impersonating bank in handle name, e.g. "sbi-kyc-dept@okaxis"
            suspicious_keywords = ["kyc", "refund", "verify", "support", "customercare", "helpdesk"]
            if any(sk in user_part for sk in suspicious_keywords):
                results.append(
                    ToolResult(
                        tool="upi_format",
                        target=upi,
                        status="warn",
                        detail=f"UPI handle '{user_part}' contains deceptive administrative keyword",
                    )
                )
            elif psp_part in valid_psp_handles:
                results.append(
                    ToolResult(
                        tool="upi_format",
                        target=upi,
                        status="ok",
                        detail=f"Valid UPI handle format on registered PSP @{psp_part}",
                    )
                )
            else:
                results.append(
                    ToolResult(
                        tool="upi_format",
                        target=upi,
                        status="ok",
                        detail=f"UPI handle on PSP @{psp_part}",
                    )
                )
        else:
            results.append(
                ToolResult(
                    tool="upi_format",
                    target=upi,
                    status="warn",
                    detail="Malformed UPI ID missing '@' separator",
                )
            )

    return results, signals


def check_payment_fields(text: str, visual_notes: List[str]) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Inspects transaction text for invalid 12-digit UPI UTRs, impossible future dates, or edited visual notes.
    States clearly what it can and cannot verify: verifies format only, never claims to confirm a payment actually happened.
    """
    results: List[ToolResult] = []
    signals: List[Signal] = []

    # 1. UPI UTR check (NPCI strictly mandates 12 digits)
    utr_match = re.search(r"(?i)(?:utr|upi\s+ref|rrn)\s*[:#\-]?\s*([a-zA-Z0-9]+)", text)
    if utr_match:
        utr_val = utr_match.group(1).strip()
        if not (utr_val.isdigit() and len(utr_val) == 12):
            signals.append(
                Signal(
                    id="PAY_INVALID_UPI_UTR",
                    label="Invalid UPI Reference Number (UTR)",
                    category="payment_screenshot",
                    weight=15.0,
                    evidence=utr_match.group(0),
                    source="tool",
                )
            )
            results.append(
                ToolResult(
                    tool="payment_fields",
                    target=utr_val,
                    status="warn",
                    detail=f"Invalid UPI UTR: expected 12 digits, found '{utr_val}'. Note: Format verification only; cannot confirm whether payment settled.",
                )
            )
        else:
            results.append(
                ToolResult(
                    tool="payment_fields",
                    target=utr_val,
                    status="ok",
                    detail=f"Valid 12-digit UPI reference format. Note: Format check only; ScamLens cannot confirm if funds actually reached your bank account.",
                )
            )

    # 2. Check for impossible or future dates in text
    date_patterns = [
        r"\b(20[2-9]\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b",  # YYYY-MM-DD
        r"\b(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[0-2])[-/](20[2-9]\d)\b",  # DD-MM-YYYY
    ]
    current_utc = datetime.now(timezone.utc)
    for pat in date_patterns:
        m = re.search(pat, text)
        if m:
            try:
                if pat.startswith(r"\b(20"):
                    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:
                    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                txn_date = datetime(year, month, day, tzinfo=timezone.utc)
                # If transaction date is in the future by more than 1 day
                if (txn_date - current_utc).total_seconds() > 86400:
                    signals.append(
                        Signal(
                            id="PAY_IMPOSSIBLE_FUTURE_TIMESTAMP",
                            label="Impossible or Future Transaction Timestamp",
                            category="payment_screenshot",
                            weight=20.0,
                            evidence=m.group(0),
                            source="tool",
                        )
                    )
                    results.append(
                        ToolResult(
                            tool="payment_fields",
                            target=m.group(0),
                            status="warn",
                            detail=f"Transaction timestamp '{m.group(0)}' is dated in the future. Note: Format check only; cannot verify bank transfer.",
                        )
                    )
                    break
            except Exception:
                pass

    # 3. Visual notes inspection for cropped status bar or edited amounts
    for note in visual_notes:
        note_lower = note.lower()
        if any(term in note_lower for term in ("cropped status bar", "edited amount", "tampered", "spoof generator")):
            signals.append(
                Signal(
                    id="PAY_EDITED_CROPPED_IMAGE",
                    label="Edited Fields or Cropped Status Bar",
                    category="payment_screenshot",
                    weight=15.0,
                    evidence=note,
                    source="tool",
                )
            )
            results.append(
                ToolResult(
                    tool="payment_fields",
                    target="image_layout",
                    status="warn",
                    detail=f"Visual tampering detected: {note}. Note: Cannot verify whether payment occurred.",
                )
            )

    return results, signals


# ------------------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------------------
async def run_verifiers(extracted: ExtractedData) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Orchestrates all external verification checks concurrently.
    Guarantees completion within 4s per check and never crashes.
    """
    tool_results: List[ToolResult] = []
    tool_signals: List[Signal] = []

    async def safe_run(coro) -> Tuple[List[ToolResult], List[Signal]]:
        try:
            return await asyncio.wait_for(coro, timeout=4.0)
        except asyncio.TimeoutError:
            return [ToolResult(tool="verifier", target="timeout", status="skipped", detail="Verifier operation timed out")], []
        except Exception as e:
            return [ToolResult(tool="verifier", target="error", status="error", detail=f"Verifier error: {e}")], []

    tasks = []

    # 1. URL Unshorten, Threat intelligence & Lookalike checks
    for url in extracted.urls:
        async def process_url(u: str):
            expanded_url, r_unshort, s_unshort = await unshorten_url(u)
            r_all = list(r_unshort)
            s_all = list(s_unshort)

            parsed_orig = urllib.parse.urlparse(u)
            domain_orig = parsed_orig.hostname or ""

            parsed = urllib.parse.urlparse(expanded_url)
            domain = parsed.hostname or ""

            domains_checked = set()
            for d in [domain_orig, domain]:
                if d and d not in domains_checked:
                    domains_checked.add(d)
                    r_look, s_look = await check_lookalike_domain(d)
                    r_all.extend(r_look)
                    s_all.extend(s_look)

            if domain:
                r_age, s_age = await check_domain_age(domain)
                r_all.extend(r_age)
                s_all.extend(s_age)

            r_gsb, s_gsb = await check_safe_browsing(expanded_url)
            r_all.extend(r_gsb)
            s_all.extend(s_gsb)

            r_urlh, s_urlh = await check_urlhaus(expanded_url)
            r_all.extend(r_urlh)
            s_all.extend(s_urlh)

            return r_all, s_all

        tasks.append(safe_run(process_url(url)))

    # Execute async tasks concurrently
    if tasks:
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in task_results:
            if isinstance(res, tuple):
                r_list, s_list = res
                tool_results.extend(r_list)
                tool_signals.extend(s_list)

    # 2. Synchronous entity validation
    r_mail, s_mail = check_free_webmail(extracted.sender, extracted.message_text, extracted.claimed_brand)
    tool_results.extend(r_mail)
    tool_signals.extend(s_mail)

    r_phone, s_phone = check_phone_format(extracted.phone_numbers)
    tool_results.extend(r_phone)
    tool_signals.extend(s_phone)

    r_upi, s_upi = check_upi_format(extracted.upi_ids)
    tool_results.extend(r_upi)
    tool_signals.extend(s_upi)

    r_pay, s_pay = check_payment_fields(extracted.message_text, extracted.visual_notes)
    tool_results.extend(r_pay)
    tool_signals.extend(s_pay)

    return tool_results, tool_signals


async def hook_verifiers(extracted: ExtractedData) -> List[ToolResult]:
    """Compatibility wrapper returning List[ToolResult]"""
    results, _ = await run_verifiers(extracted)
    return results
