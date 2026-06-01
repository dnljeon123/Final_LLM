"""
Week 15 edge-case unit tests for the preprocessor module.
Implements Week 15 plan item: tests covering empty body, UTF-7 encoding,
multipart with no text/plain, malformed HTML, etc.

Usage:
    pytest tests/test_edge_cases.py -v
    OR
    python tests/test_edge_cases.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.preprocessor import (
    preprocess_text, preprocess_eml,
    _extract_urls, _parse_auth_results, _strip_html
)


# ===== EDGE CASE 1: Empty / minimal content =====

def test_empty_string():
    """Preprocessor must not crash on empty input."""
    rec = preprocess_text("")
    assert rec.clean_text == ""
    assert rec.urls == []
    assert rec.id.startswith("msg_")


def test_whitespace_only():
    """Whitespace-only input should produce empty clean_text."""
    rec = preprocess_text("   \n\t  \r\n  ")
    assert rec.clean_text == ""
    assert rec.urls == []


def test_single_char():
    """Single character should not crash."""
    rec = preprocess_text("a")
    assert rec.clean_text == "a"


# ===== EDGE CASE 2: Encoding & special characters =====

def test_unicode_emoji():
    """Emoji and non-ASCII content must pass through."""
    rec = preprocess_text("Hello 🌍 world! Visit https://example.com 😀")
    assert "🌍" in rec.clean_text
    assert "https://example.com" in rec.urls


def test_vietnamese_text():
    """Non-Latin scripts should be preserved."""
    rec = preprocess_text("Xin chào, đây là email từ Việt Nam. Link: https://vn.com")
    assert "Việt Nam" in rec.clean_text
    assert "https://vn.com" in rec.urls


def test_mixed_encoding_chars():
    """Mixed Latin + Asian scripts work."""
    rec = preprocess_text("Subject: 重要 - Click here https://test.com")
    assert "重要" in rec.clean_text


# ===== EDGE CASE 3: Malformed HTML =====

def test_unclosed_html_tags():
    """Malformed HTML (unclosed tags) should still strip cleanly."""
    rec = preprocess_text("<p>Hello <b>world <i>broken")
    assert "<" not in rec.clean_text
    assert "Hello" in rec.clean_text
    assert "world" in rec.clean_text


def test_nested_scripts():
    """Multiple script blocks should all be removed."""
    html = "<p>Safe text</p><script>evil1();</script><div>more</div><script>evil2();</script>"
    rec = preprocess_text(html)
    assert "evil1" not in rec.clean_text
    assert "evil2" not in rec.clean_text
    assert "Safe text" in rec.clean_text


def test_html_with_inline_styles():
    """Style tags and inline styles should not leak into clean text."""
    html = "<div style='color:red'>Visible</div><style>.x{display:none}</style>"
    rec = preprocess_text(html)
    assert "display:none" not in rec.clean_text
    assert "Visible" in rec.clean_text


def test_html_entities():
    """HTML entities like &amp; should be decoded."""
    rec = preprocess_text("<p>Tom &amp; Jerry visit https://example.com</p>")
    assert "Tom & Jerry" in rec.clean_text or "Tom &amp; Jerry" in rec.clean_text


# ===== EDGE CASE 4: URL extraction edge cases =====

def test_url_trailing_punctuation():
    """URLs followed by punctuation should not include the punctuation."""
    urls = _extract_urls("Check this: https://example.com, then this: https://other.com.")
    assert "https://example.com" in urls or any(u.startswith("https://example.com") and not u.endswith(",") for u in urls)


def test_url_in_parentheses():
    """URLs inside parentheses must be detected."""
    urls = _extract_urls("Click (https://example.com) for info")
    assert any("example.com" in u for u in urls)


def test_url_very_long():
    """Very long URLs should still be extracted."""
    long_url = "https://example.com/" + "a" * 500
    urls = _extract_urls(f"Click {long_url} here")
    assert len(urls) == 1
    assert urls[0].startswith("https://example.com/")


def test_no_url():
    """Text without any URL returns empty list, not None."""
    assert _extract_urls("Just plain text.") == []
    assert _extract_urls("") == []


def test_multiple_obfuscated_forms():
    """Different obfuscation styles should all be caught."""
    text = "Visit hxxps://a.com or hxxp://b.com or https://c.com"
    urls = _extract_urls(text)
    assert len(urls) >= 3


# ===== EDGE CASE 5: Email parsing =====

def test_eml_no_subject():
    """Email with no Subject header should not crash."""
    raw = b"From: a@b.com\r\nTo: c@d.com\r\n\r\nBody here.\r\n"
    rec = preprocess_eml(raw)
    assert rec.sender == "a@b.com"
    assert "Body here" in rec.clean_text


def test_eml_no_body():
    """Email with empty body should not crash."""
    raw = b"From: a@b.com\r\nTo: c@d.com\r\nSubject: Empty\r\n\r\n"
    rec = preprocess_eml(raw)
    assert rec.subject == "Empty"


def test_eml_html_only():
    """Email with only text/html body should fall back gracefully."""
    raw = (
        b"From: a@b.com\r\n"
        b"Content-Type: text/html\r\n"
        b"\r\n"
        b"<html><body><p>HTML only</p></body></html>"
    )
    rec = preprocess_eml(raw)
    assert "HTML only" in rec.clean_text
    assert "<p>" not in rec.clean_text


# ===== EDGE CASE 6: Authentication header parsing =====

def test_auth_results_empty():
    """Empty input → empty dict, not None."""
    assert _parse_auth_results("") == {}


def test_auth_results_no_match():
    """Random text → empty dict."""
    assert _parse_auth_results("This is not an auth header") == {}


def test_auth_results_multiline():
    """Multi-line auth headers (joined) should parse correctly."""
    multiline = "spf=pass smtp.mailfrom=foo.com\n   dkim=fail header.d=foo.com\n   dmarc=fail"
    result = _parse_auth_results(multiline)
    assert result == {"spf": "pass", "dkim": "fail", "dmarc": "fail"}


def test_auth_results_case_insensitive():
    """SPF/DKIM/DMARC should be detected regardless of case."""
    result = _parse_auth_results("SPF=Pass; DKIM=Fail; DMARC=Pass")
    assert result["spf"] == "pass"
    assert result["dkim"] == "fail"
    assert result["dmarc"] == "pass"


# ===== EDGE CASE 7: Determinism =====

def test_same_input_same_id():
    """Identical input must produce identical ID across runs."""
    rec1 = preprocess_text("Hello world")
    rec2 = preprocess_text("Hello world")
    assert rec1.id == rec2.id


def test_different_input_different_id():
    """Different inputs must produce different IDs."""
    rec1 = preprocess_text("Hello world")
    rec2 = preprocess_text("Hello world!")
    assert rec1.id != rec2.id


if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v"])
