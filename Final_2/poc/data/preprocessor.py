"""
Data preprocessing module — Member 1's responsibility.

Converts heterogeneous raw inputs (.eml files, plain text, CSV rows) into
a unified Record dataclass that downstream LLM analysis can consume.
"""
from __future__ import annotations

import email
import hashlib
import re
from dataclasses import dataclass, field, asdict
from email import policy
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


URL_REGEX = re.compile(
    r"https?://[^\s<>\"']+|hxxps?://[^\s<>\"']+|"
    r"www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s<>\"']*",
    re.IGNORECASE,
)

AUTH_HEADER_REGEX = re.compile(
    r"(spf|dkim|dmarc)\s*=\s*(pass|fail|none|neutral|softfail|temperror|permerror)",
    re.IGNORECASE,
)


@dataclass
class Record:
    """Unified message representation that all downstream modules consume."""
    id: str
    source_format: str  # "eml" | "csv_sms" | "plain"
    raw_text: str
    clean_text: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    urls: list[str] = field(default_factory=list)
    auth_status: dict[str, str] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    label: Optional[int] = None  # 1=phishing, 0=legitimate, None=unlabeled

    def to_dict(self) -> dict:
        return asdict(self)

    def llm_input_text(self) -> str:
        """Build the compact representation that gets sent to the LLM."""
        parts = []
        if self.sender:
            parts.append(f"From: {self.sender}")
        if self.subject:
            parts.append(f"Subject: {self.subject}")
        if self.auth_status:
            auth = ", ".join(f"{k}={v}" for k, v in self.auth_status.items())
            parts.append(f"Auth: {auth}")
        if self.urls:
            parts.append(f"URLs: {', '.join(self.urls[:10])}")
        parts.append("")
        parts.append("Body:")
        parts.append(self.clean_text)
        return "\n".join(parts)


def _hash_id(text: str) -> str:
    return "msg_" + hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:10]


def _strip_html(html: str) -> str:
    if not html or "<" not in html:
        return html
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove scripts and styles entirely
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        # Fallback: aggressive regex strip
        return re.sub(r"<[^>]+>", " ", html)


def _extract_urls(text: str) -> list[str]:
    """Extract unique URLs, including obfuscated forms like hxxp."""
    if not text:
        return []
    found = URL_REGEX.findall(text)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for u in found:
        normalized = u.strip(".,;:!?)")
        if normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def _parse_auth_results(headers_text: str) -> dict[str, str]:
    """Parse Authentication-Results header into a dict like {spf: pass, dkim: fail}."""
    result = {}
    for match in AUTH_HEADER_REGEX.finditer(headers_text):
        proto, status = match.group(1).lower(), match.group(2).lower()
        if proto not in result:  # first occurrence wins
            result[proto] = status
    return result


def preprocess_eml(raw_bytes: bytes, label: Optional[int] = None) -> Record:
    """Preprocess raw .eml bytes into a Record."""
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)

    subject = str(msg.get("Subject", "")) or None
    sender = str(msg.get("From", "")) or None
    recipient = str(msg.get("To", "")) or None
    date = str(msg.get("Date", ""))

    # Auth-Results header may appear multiple times
    auth_headers = "\n".join(str(v) for v in msg.get_all("Authentication-Results", []) or [])
    auth_status = _parse_auth_results(auth_headers)

    # Extract body — prefer text/plain, fall back to text/html
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    body_text = part.get_content()
                    break
                except Exception:
                    continue
        if not body_text:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        body_text = _strip_html(part.get_content())
                        break
                    except Exception:
                        continue
    else:
        try:
            body_text = msg.get_content()
            if msg.get_content_type() == "text/html":
                body_text = _strip_html(body_text)
        except Exception:
            body_text = raw_bytes.decode("utf-8", errors="ignore")

    body_text = (body_text or "").strip()
    raw_text = raw_bytes.decode("utf-8", errors="ignore")

    # URL extraction: scan both clean body and raw (some URLs live in headers)
    urls = list(dict.fromkeys(_extract_urls(body_text) + _extract_urls(raw_text)))[:25]

    return Record(
        id=_hash_id(raw_text),
        source_format="eml",
        raw_text=raw_text,
        clean_text=body_text,
        subject=subject,
        sender=sender,
        recipient=recipient,
        urls=urls,
        auth_status=auth_status,
        metadata={"date": date},
        label=label,
    )


def preprocess_text(text: str, label: Optional[int] = None) -> Record:
    """Preprocess a plain text message (e.g., SMS, pasted content)."""
    clean = _strip_html(text) if "<" in text else text
    clean = re.sub(r"\s+", " ", clean).strip()
    return Record(
        id=_hash_id(clean),
        source_format="plain",
        raw_text=text,
        clean_text=clean,
        urls=_extract_urls(text),
        label=label,
    )


def preprocess(source: str | bytes | Path, label: Optional[int] = None) -> Record:
    """Main entry point: detect format and dispatch."""
    if isinstance(source, Path) or (isinstance(source, str) and source.endswith(".eml")):
        path = Path(source)
        if path.exists():
            return preprocess_eml(path.read_bytes(), label=label)
    if isinstance(source, bytes):
        return preprocess_eml(source, label=label)
    if isinstance(source, str):
        return preprocess_text(source, label=label)
    raise TypeError(f"Unsupported source type: {type(source)}")
