"""
Link Checker Service
-------------------
Heuristic and deterministic link analysis for phishing, scam, and brand impersonation lures.
Ports and extends the logic from scam-link-checker.html into Python with strict evidence quoting
and full integration into ScamLens's ToolResult and Signal schemas.
"""

from datetime import datetime, timezone
import ipaddress
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import urllib.parse

from app.schemas import ExtractedData, Signal, ToolResult


BRANDS: Dict[str, List[str]] = {
    "paypal": ["paypal.com"],
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amazon.de", "amazon.ca", "amazon.com.au"],
    "google": ["google.com", "google.co.in", "gmail.com"],
    "flipkart": ["flipkart.com"],
    "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"],
    "gpay": ["pay.google.com"],
    "netflix": ["netflix.com"],
    "apple": ["apple.com", "icloud.com"],
    "microsoft": ["microsoft.com", "live.com", "office.com"],
    "facebook": ["facebook.com", "fb.com"],
    "instagram": ["instagram.com"],
    "whatsapp": ["whatsapp.com", "wa.me"],
    "irctc": ["irctc.co.in"],
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "sbicard.com"],
    "hdfc": ["hdfcbank.com", "hdfc.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "kotak": ["kotak.com"],
    "binance": ["binance.com"],
    "coinbase": ["coinbase.com"],
    "ebay": ["ebay.com"],
    "dhl": ["dhl.com"],
    "fedex": ["fedex.com"],
    "myntra": ["myntra.com"],
    "swiggy": ["swiggy.com"],
    "zomato": ["zomato.com"],
    "uidai": ["uidai.gov.in"],
    "incometax": ["incometax.gov.in"],
    "airtel": ["airtel.in"],
    "jio": ["jio.com"],
    "bankofindia": ["bankofindia.co.in"],
}

BAD_TLDS: Set[str] = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "buzz", "icu",
    "work", "rest", "loan", "zip", "mov", "cfd", "sbs", "monster", "cyou",
    "quest", "fit", "cam", "support", "bid", "win", "vip", "live", "site",
    "online", "store", "shop",
}

SHORTENERS: Set[str] = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "rb.gy", "shorturl.at", "ow.ly", "rebrand.ly", "tiny.cc", "s.id", "t.ly",
}

BAIT_WORDS: List[str] = [
    "login", "signin", "verify", "verification", "secure", "update", "account",
    "bonus", "prize", "winner", "free", "gift", "claim", "kyc", "refund",
    "lottery", "giveaway", "recharge", "offer", "earn", "wallet", "crypto",
    "invest", "double", "reward", "suspend", "unlock", "confirm", "cashback",
    "lucky", "airdrop", "password", "otp",
]

TWO_PART_TLDS: Set[str] = {
    "co.in", "org.in", "net.in", "gov.in", "nic.in", "ac.in", "edu.in", "res.in",
    "co.uk", "org.uk", "ac.uk", "com.au", "co.nz", "com.br", "co.za", "co.jp", "com.sg",
}


def get_registered_domain(host: str) -> str:
    """Extract registered domain (e.g., 'amazon.co.in' from 'pay.amazon.co.in')."""
    parts = host.lower().strip(".").split(".")
    if len(parts) <= 2:
        return host
    last2 = ".".join(parts[-2:])
    if last2 in TWO_PART_TLDS:
        return ".".join(parts[-3:])
    return last2


def normalize_homoglyphs(text: str) -> str:
    """Replaces common visual substitutions (e.g., rn -> m, 0 -> o)."""
    return (
        text.replace("rn", "m")
        .replace("vv", "w")
        .replace("0", "o")
        .replace("1", "l")
        .replace("3", "e")
        .replace("5", "s")
        .replace("$", "s")
    )


def is_ip_host(host: str) -> bool:
    """Check if host is an IPv4 or IPv6 address."""
    clean_host = host.strip("[]")
    try:
        ipaddress.ip_address(clean_host)
        return True
    except ValueError:
        return False


def is_likely_url(text: str) -> bool:
    """Detects if a string is or contains a standalone URL."""
    s = text.strip()
    if re.match(r"^(?:https?:\/\/|www\.)[^\s]+$", s, re.IGNORECASE):
        return True
    if re.search(r"\bhttps?:\/\/[^\s]+", s, re.IGNORECASE):
        return True
    if re.match(r"^[a-zA-Z0-9-]+\.(?:com|org|net|in|co\.in|xyz|top|gov\.in)[^\s]*$", s, re.IGNORECASE):
        return True
    return False


def analyze_link(raw_url: str) -> Optional[Dict[str, Any]]:
    """
    Performs full heuristic scam link analysis on a raw URL.
    Returns structured results including score (0-100), level, and individual findings.
    """
    s = raw_url.strip()
    if not s:
        return None

    had_protocol = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:\/\/", s))
    full_candidate = s if had_protocol else "https://" + s

    try:
        parsed = urllib.parse.urlsplit(full_candidate)
    except Exception:
        return None

    if parsed.scheme.lower() not in ("http", "https"):
        return None

    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return None

    full_path_query = (host + (parsed.path or "") + ("?" + parsed.query if parsed.query else "")).lower()

    findings: List[Dict[str, Any]] = []
    score = 0

    def add_finding(level: str, title: str, description: str, points: int):
        nonlocal score
        findings.append({
            "level": level,
            "title": title,
            "description": description,
            "points": points,
        })
        score += points

    reg_domain = get_registered_domain(host)
    label = reg_domain.split(".")[0] if "." in reg_domain else reg_domain
    tld = host.split(".")[-1] if "." in host else ""

    # Check known official brand domain
    trusted_brand: Optional[str] = None
    for brand, domains in BRANDS.items():
        if reg_domain in domains:
            trusted_brand = brand
            break

    # 1. Scheme check
    if parsed.scheme.lower() == "http":
        add_finding(
            "bad",
            "Not encrypted (http)",
            "The page doesn't use a secure connection, so anything you type can be read in transit. Real shops and banks use https.",
            20,
        )
    else:
        add_finding(
            "good",
            "Uses https",
            "The connection is encrypted. Note: Scam sites can also use https, so it is not sole proof of safety.",
            0,
        )

    # 2. IP Host
    if is_ip_host(host) or re.match(r"^0x[0-9a-f]+$", host):
        add_finding(
            "bad",
            "Address is a number, not a name",
            f"Host is a raw IP address ({host}). Legitimate institutions almost never ask users to log in or pay at a numeric IP.",
            40,
        )

    # 3. Punycode / IDN lookalikes
    if "xn--" in host:
        add_finding(
            "bad",
            "Look-alike characters in the name",
            "The domain uses special Unicode/punycode characters that imitate letters, a common technique for spoofing real brands.",
            35,
        )

    # 4. Embedded @ character before hostname
    if "@" in s.split("://")[-1].split("/")[0]:
        add_finding(
            "bad",
            "Contains '@' before the site name",
            "Everything before '@' is treated as credentials and ignored by the browser, obscuring the true destination.",
            35,
        )

    # 5. Shortened URL
    if host in SHORTENERS or reg_domain in SHORTENERS:
        add_finding(
            "warn",
            "Shortened link",
            "The link uses an unexpanded URL shortener. You cannot see the destination domain without expanding it first.",
            25,
        )

    # 6. Unusual port
    if parsed.port and parsed.port not in (80, 443):
        add_finding(
            "warn",
            "Unusual port number",
            f"Port {parsed.port} is rarely used by genuine consumer websites or banking portals.",
            15,
        )

    # 7. Brand impersonation vs official domains
    if trusted_brand:
        add_finding(
            "good",
            f"Matches the official domain for {trusted_brand.upper()}",
            f"The registered domain is '{reg_domain}', which is a known official address for {trusted_brand.upper()}.",
            -30,
        )
        extra = host[: len(host) - len(reg_domain) - 1]
        if extra and re.search(r"(login|secure|verify|account|update)", extra) and extra.count(".") >= 1:
            add_finding(
                "warn",
                "Odd sub-domain wording",
                "Official root domain, but the sub-domain contains security-sounding words. Verify you arrived through the official app.",
                10,
            )
    else:
        brand_hit: Optional[str] = None
        for b in BRANDS.keys():
            if b in host:
                brand_hit = b
                break

        if brand_hit:
            official = BRANDS[brand_hit][0]
            add_finding(
                "bad",
                f"Uses the name '{brand_hit.upper()}' but isn't their domain",
                f"The legitimate {brand_hit.upper()} site is '{official}'. This link is hosted on '{reg_domain}'. Scammers frequently stuff brand names into deceptive subdomains.",
                40,
            )
        else:
            norm_label = normalize_homoglyphs(label)
            if norm_label != label:
                for b in BRANDS.keys():
                    if b in norm_label:
                        add_finding(
                            "bad",
                            f"Looks like a misspelt copy of '{b.upper()}'",
                            f"Domain label '{label}' visually mimics '{b}'. Character substitutions (e.g. 0 for o, rn for m) are typical spoofing tactics.",
                            40,
                        )
                        break

    # 8. Suspicious / throwaway TLD
    if tld in BAD_TLDS:
        add_finding(
            "warn",
            f"Ending '.{tld}' is common on throw-away sites",
            f"Cheap or free domain endings (.{tld}) are heavily utilized in mass phishing campaigns.",
            15,
        )

    # 9. Excessive subdomains
    dots = host.count(".")
    if dots >= 4:
        add_finding(
            "warn",
            "Many sub-domains",
            f"The address has {dots + 1} parts. Scammers add extra prefixes to bury the true destination at the end.",
            15,
        )

    # 10. Hyphen count
    hyphens = host.count("-")
    if hyphens >= 3:
        add_finding(
            "warn",
            "Lots of hyphens in the name",
            "Names with multiple hyphens (e.g. 'secure-login-bank-offer') are frequently registered for disposable scams.",
            15,
        )
    elif hyphens >= 1 and not trusted_brand:
        add_finding(
            "warn",
            "Hyphenated domain",
            "Hyphens in domain names are a mild caution indicator when combined with urgency or financial bait.",
            5,
        )

    # 11. Excess digits
    digits = len(re.findall(r"\d", label))
    if digits >= 4:
        add_finding(
            "warn",
            "Many digits in the name",
            "Random strings of numbers in domain names often indicate auto-generated disposable infrastructure.",
            10,
        )

    # 12. Pressure / bait words
    found_words = [w for w in BAIT_WORDS if w in full_path_query]
    if found_words and not trusted_brand:
        preview = ", ".join(found_words[:5])
        penalty = min(30, len(found_words) * 12)
        add_finding(
            "bad" if len(found_words) >= 2 else "warn",
            f"Pressure or bait words: {preview}",
            "Words regarding free gifts, KYC updates, refunds, or account blocks are used by scammers to manipulate targets into hasty action.",
            penalty,
        )

    # 13. Very long URL
    if len(s) > 120:
        add_finding(
            "warn",
            "Very long link",
            f"Link length is {len(s)} characters. Abnormally long addresses are sometimes constructed to obscure malicious parameters.",
            10,
        )

    # 14. Heavy percent-encoding
    encoded_matches = re.findall(r"%[0-9a-f]{2}", full_path_query, re.IGNORECASE)
    if len(encoded_matches) > 5:
        add_finding(
            "warn",
            "Heavy encoding in the link",
            "Excessive percent-encoded hex sequences can be used to bypass simple text filters.",
            10,
        )

    # 15. Executable / APK file download
    if re.search(r"\.(apk|exe|scr|msi|bat|jar|cmd)(?:\?|$)", parsed.path.lower()):
        add_finding(
            "bad",
            "Link downloads an app or program file",
            "The link points directly to an installable package (.apk / .exe). Never download or sideload apps from links sent via chat or SMS.",
            40,
        )

    clamped_score = max(0, min(100, score))
    level = "bad" if clamped_score >= 45 else ("warn" if clamped_score >= 20 else "good")
    title = {
        "bad": "Very likely fake or unsafe",
        "warn": "Suspicious: be careful",
        "good": "No obvious red flags",
    }[level]

    advice = (
        "Still, don't enter passwords, card details, or OTPs unless you reached the site from the company's official app or by typing its address yourself."
        if level == "good"
        else "Don't enter any personal details, passwords, card numbers, or OTPs, and do not pay anything. If someone sent you this link, treat the sender with extreme suspicion."
    )

    encoded_url = urllib.parse.quote(parsed.geturl(), safe="")
    encoded_reg = urllib.parse.quote(reg_domain, safe="")

    second_opinions = [
        {"name": "Google Safe Browsing", "url": f"https://transparencyreport.google.com/safe-browsing/search?url={encoded_url}"},
        {"name": "VirusTotal", "url": "https://www.virustotal.com/gui/home/url"},
        {"name": "Domain Age (WHOIS)", "url": f"https://who.is/whois/{encoded_reg}"},
    ]

    return {
        "url": parsed.geturl(),
        "host": host,
        "reg_domain": reg_domain,
        "score": clamped_score,
        "level": level,
        "title": title,
        "trusted": bool(trusted_brand),
        "trusted_brand": trusted_brand,
        "findings": findings,
        "advice": advice,
        "second_opinions": second_opinions,
    }


def run_link_checker(extracted: ExtractedData) -> Tuple[List[ToolResult], List[Signal]]:
    """
    Evaluates all URLs in ExtractedData through the Link Checker.
    Converts heuristic detections into ScamLens ToolResult and Signal objects.
    """
    tool_results: List[ToolResult] = []
    signals: List[Signal] = []

    urls_to_check: List[str] = list(extracted.urls)

    # Check if raw message contains unparsed URLs
    found_urls = re.findall(r"https?://[^\s<>\"']+", extracted.message_text)
    for u in found_urls:
        if u not in urls_to_check:
            urls_to_check.append(u)

    for target_url in urls_to_check[:5]:
        analysis = analyze_link(target_url)
        if not analysis:
            continue

        host = analysis["host"]
        level = analysis["level"]
        score = analysis["score"]

        status = "warn" if level in ("bad", "warn") else "ok"
        tool_results.append(
            ToolResult(
                tool="scam_link_checker",
                target=target_url,
                status=status,
                detail=f"{analysis['title']} (Score {score}/100, Host: {host})",
            )
        )

        for finding in analysis["findings"]:
            if finding["level"] in ("bad", "warn"):
                signals.append(
                    Signal(
                        id=f"LINK_HEURISTIC_{finding['title'].replace(' ', '_').upper()[:30]}",
                        label=finding["title"],
                        category="links",
                        weight=float(finding["points"]),
                        evidence=f'"{target_url}" -> {finding["description"]}',
                        source="tool",
                    )
                )
            elif finding["level"] == "good" and finding["points"] < 0:
                signals.append(
                    Signal(
                        id="LINK_OFFICIAL_DOMAIN_MATCH",
                        label=finding["title"],
                        category="links",
                        weight=float(finding["points"]),
                        evidence=f'"{target_url}" verified official domain for {analysis.get("trusted_brand", "brand").upper()}',
                        source="tool",
                    )
                )

    return tool_results, signals
