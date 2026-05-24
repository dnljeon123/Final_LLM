"""Basic tests that run without an API key (mocks the LLM)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.preprocessor import preprocess_text, preprocess_eml, _extract_urls, _parse_auth_results
from llm.schema import parse_llm_response, Prediction
from llm.prompts import get_strategy
from eval.metrics import compute_metrics


# ---- Preprocessor tests ----

def test_extract_urls_basic():
    text = "Click https://example.com and also http://foo.bar/path?x=1"
    urls = _extract_urls(text)
    assert "https://example.com" in urls
    assert any("foo.bar" in u for u in urls)


def test_extract_urls_obfuscated():
    text = "Visit hxxps://bad-site.com/login"
    urls = _extract_urls(text)
    assert any("bad-site.com" in u for u in urls)


def test_extract_urls_dedupe():
    text = "https://x.com and https://x.com again"
    urls = _extract_urls(text)
    assert urls.count("https://x.com") == 1


def test_parse_auth_results():
    h = "spf=pass smtp.mailfrom=foo.com; dkim=fail; dmarc=fail"
    auth = _parse_auth_results(h)
    assert auth == {"spf": "pass", "dkim": "fail", "dmarc": "fail"}


def test_preprocess_text_plain():
    rec = preprocess_text("Hello world, visit https://example.com", label=0)
    assert rec.source_format == "plain"
    assert rec.label == 0
    assert "https://example.com" in rec.urls
    assert rec.id.startswith("msg_")


def test_preprocess_text_html_stripping():
    rec = preprocess_text("<p>Hello <b>world</b></p><script>alert(1)</script>")
    assert "alert" not in rec.clean_text
    assert "Hello" in rec.clean_text


def test_preprocess_eml_minimal():
    raw = (
        b"From: alice@example.com\r\n"
        b"To: bob@example.com\r\n"
        b"Subject: Test\r\n"
        b"\r\n"
        b"This is a test email body.\r\n"
    )
    rec = preprocess_eml(raw, label=0)
    assert rec.source_format == "eml"
    assert rec.subject == "Test"
    assert "alice@example.com" in rec.sender


# ---- Schema tests ----

def test_parse_llm_response_valid():
    raw = '{"label": "phishing", "confidence": 0.92, "red_flags": ["urgency"], "reasoning": "Test."}'
    pred = parse_llm_response(raw)
    assert pred.label == "phishing"
    assert pred.confidence == 0.92
    assert pred.red_flags == ["urgency"]
    assert pred.label_binary == 1


def test_parse_llm_response_safe_is_zero():
    raw = '{"label": "safe", "confidence": 0.95, "red_flags": [], "reasoning": "ok"}'
    pred = parse_llm_response(raw)
    assert pred.label_binary == 0


def test_parse_llm_response_strips_fences():
    raw = '```json\n{"label": "safe", "confidence": 1.0, "red_flags": [], "reasoning": "x"}\n```'
    pred = parse_llm_response(raw)
    assert pred.label == "safe"


def test_parse_llm_response_clamps_confidence():
    raw = '{"label": "phishing", "confidence": 1.5, "red_flags": [], "reasoning": "x"}'
    pred = parse_llm_response(raw)
    assert pred.confidence == 1.0


def test_parse_llm_response_invalid_label_raises():
    import pytest
    raw = '{"label": "maybe", "confidence": 0.5, "red_flags": [], "reasoning": "x"}'
    with __import__("pytest").raises(ValueError):
        parse_llm_response(raw)


# ---- Prompt tests ----

def test_get_strategy_aliases():
    assert get_strategy("cot") is get_strategy("chain_of_thought")
    assert get_strategy("zero_shot") is get_strategy("ZERO-SHOT")


def test_strategy_returns_two_strings():
    sys_, user = get_strategy("zero_shot")("hello")
    assert isinstance(sys_, str) and len(sys_) > 0
    assert isinstance(user, str) and "hello" in user


# ---- Metrics tests ----

def test_metrics_perfect():
    m = compute_metrics([1, 0, 1, 0], [1, 0, 1, 0])
    assert m.accuracy == 1.0
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.f1 == 1.0


def test_metrics_all_wrong():
    m = compute_metrics([1, 0, 1, 0], [0, 1, 0, 1])
    assert m.accuracy == 0.0
    assert m.f1 == 0.0


def test_metrics_mixed():
    # 2 TP, 1 FN, 1 FP, 0 TN
    m = compute_metrics([1, 1, 1, 0], [1, 1, 0, 1])
    assert m.tp == 2 and m.fn == 1 and m.fp == 1 and m.tn == 0
    assert m.precision == 2 / 3
    assert m.recall == 2 / 3


if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v"])
