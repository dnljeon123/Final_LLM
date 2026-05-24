"""
Data Preprocessing Module (Owner: Member 1)
Handles ingestion and feature extraction from raw messages.
"""
import email
import hashlib
import re
from email.policy import default as default_policy
from typing import Optional

import tldextract
from bs4 import BeautifulSoup

# Known URL shorteners
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly"}

# Suspicious TLDs (often used in phishing)
SUS_TLDS = {"tk", "ml", "ga", "cf", "click", "download", "loan", "review"}

# Top brand domains for homoglyph detection
BRAND_DOMAINS = {
    "google", "facebook", "amazon", "paypal", "microsoft", "apple",
    "netflix", "instagram", "linkedin", "twitter", "youtube", "bank"
}


def load_eml(file_path: str) -> dict:
    """Load .eml file and extract structured fields."""
    with open(file_path, "rb") as f:
        msg = email.message_from_bytes(f.read(), policy=default_policy)
    return {
        "id": hashlib.md5(file_path.encode()).hexdigest()[:12],
        "type": "email",
        "raw_content": msg.as_string(),
        "headers": _extract_headers(msg),
        "body": _extract_body(msg),
    }


def _extract_headers(msg) -> dict:
    return {
        "from": str(msg.get("From", "")),
        "reply_to": str(msg.get("Reply-To", "")),
        "subject": str(msg.get("Subject", "")),
        "received": [str(h) for h in msg.get_all("Received", [])],
        "auth_results": str(msg.get("Authentication-Results", "")),
    }


def _extract_body(msg) -> str:
    """Walk through message parts, prefer text/plain, fallback to HTML stripped."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                return part.get_content()
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return BeautifulSoup(part.get_content(), "html.parser").get_text()
    else:
        content = msg.get_content()
        if msg.get_content_type() == "text/html":
            return BeautifulSoup(content, "html.parser").get_text()
        return content
    return ""


def clean_text(text: str) -> str:
    """Normalize whitespace, strip HTML residue."""
    text = BeautifulSoup(text, "html.parser").get_text() if "<" in text else text
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_urls(text: str) -> list[dict]:
    """Extract and analyze all URLs in the text."""
    url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
    urls = url_pattern.findall(text)
    return [analyze_url(u) for u in urls]


def analyze_url(url: str) -> dict:
    """Analyze a single URL for suspicious indicators."""
    parsed = tldextract.extract(url)
    domain = parsed.domain.lower()
    suffix = parsed.suffix.lower()
    indicators = []

    if parsed.domain in SHORTENERS:
        indicators.append("url_shortener")
    if suffix in SUS_TLDS:
        indicators.append("suspicious_tld")
    if _is_ip_address(url):
        indicators.append("ip_address_url")
    if _detect_homoglyph(domain):
        indicators.append("homoglyph_attack")
    if domain.count("-") > 2:
        indicators.append("excessive_hyphens")

    return {
        "url": url,
        "domain": f"{parsed.domain}.{parsed.suffix}",
        "suspicious_indicators": indicators,
    }


def _is_ip_address(url: str) -> bool:
    return bool(re.search(r"https?://\d+\.\d+\.\d+\.\d+", url))


def _detect_homoglyph(domain: str) -> Optional[str]:
    """Simple homoglyph: digit substitution check."""
    substitutions = str.maketrans("01l", "olI")
    normalized = domain.translate(substitutions)
    for brand in BRAND_DOMAINS:
        if normalized.lower() == brand and domain.lower() != brand:
            return brand
    return None


def check_header_mismatch(headers: dict) -> bool:
    """Check if From and Reply-To domains differ."""
    from_addr = headers.get("from", "")
    reply_to = headers.get("reply_to", "")
    if not reply_to:
        return False

    def extract_domain(addr):
        match = re.search(r"@([\w.-]+)", addr)
        return match.group(1).lower() if match else None

    return extract_domain(from_addr) != extract_domain(reply_to)


def process(raw_message: dict) -> dict:
    """
    Main preprocessing entry point.
    Input: {type, raw_content, [headers if email]}
    Output: unified preprocessed dict for LLM consumption.
    """
    msg_type = raw_message.get("type", "text")
    raw = raw_message.get("raw_content", "")

    if msg_type == "email" and "headers" in raw_message:
        body = raw_message.get("body", raw)
        headers = raw_message["headers"]
    else:
        body = raw
        headers = {}

    cleaned = clean_text(body)
    urls = extract_urls(cleaned)

    return {
        "id": raw_message.get("id", hashlib.md5(raw.encode()).hexdigest()[:12]),
        "type": msg_type,
        "cleaned_text": cleaned,
        "urls": urls,
        "headers": headers,
        "from_reply_mismatch": check_header_mismatch(headers) if headers else False,
        "char_count": len(cleaned),
        "url_count": len(urls),
        "suspicious_url_count": sum(1 for u in urls if u["suspicious_indicators"]),
    }
