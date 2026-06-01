"""
Member 1 — Data Engineer's experimental script.
Run this script to collect real measurements for the Week 14/15 report.

Usage:
    python member1_experiments.py
"""
import time
import statistics
from pathlib import Path

from data import preprocess_text, load_samples
from data.preprocessor import _extract_urls, _parse_auth_results


def experiment_1_url_extraction():
    """Experiment 1: Measure URL extraction accuracy across tricky formats."""
    print("\n=== Experiment 1: URL Extraction ===")

    test_cases = [
        ("Click https://example.com here", ["https://example.com"]),
        ("Obfuscated: hxxps://bad-site.com/login", ["hxxps://bad-site.com/login"]),
        ("Multiple: http://a.com and https://b.com and http://a.com", 2),  # dedupe
        ("With dots: www.example.co.uk/path", 1),
        ("No URL here", 0),
        ("Defanged hxxp://evil.com/", 1),
    ]

    for text, expected in test_cases:
        urls = _extract_urls(text)
        result = "PASS" if (isinstance(expected, list) and urls == expected) or \
                           (isinstance(expected, int) and len(urls) == expected) else "FAIL"
        print(f"  [{result}] {text[:50]:50s} -> {urls}")


def experiment_2_auth_parsing():
    """Experiment 2: Parse email authentication headers (SPF/DKIM/DMARC)."""
    print("\n=== Experiment 2: SPF/DKIM/DMARC Parsing ===")

    headers = [
        "spf=pass smtp.mailfrom=foo.com; dkim=pass header.d=foo.com; dmarc=pass",
        "spf=fail; dkim=fail; dmarc=fail action=quarantine",
        "spf=pass; dkim=none",
        "Random text with no auth info",
    ]

    for h in headers:
        result = _parse_auth_results(h)
        print(f"  Input:  {h[:60]}")
        print(f"  Output: {result}\n")


def experiment_3_preprocess_speed():
    """Experiment 3: Measure preprocessing latency across the 6 demo samples."""
    print("\n=== Experiment 3: Preprocessing Speed ===")

    samples = load_samples()
    if not samples:
        print("  No samples found.")
        return

    times = []
    for s in samples:
        start = time.perf_counter()
        # Re-process to measure
        _ = preprocess_text(s.raw_text, label=s.label)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        name = s.metadata.get("sample_name", s.id)
        print(f"  {name:35s} {elapsed:6.2f} ms  ({len(s.clean_text)} chars clean)")

    print(f"\n  Mean: {statistics.mean(times):.2f} ms")
    print(f"  Min:  {min(times):.2f} ms | Max: {max(times):.2f} ms")


def experiment_4_dataset_statistics():
    """Experiment 4: Dataset statistics — numbers to drop into the report."""
    print("\n=== Experiment 4: Dataset Statistics ===")

    samples = load_samples()
    phishing = [s for s in samples if s.label == 1]
    legit = [s for s in samples if s.label == 0]

    print(f"  Total samples:             {len(samples)}")
    print(f"  Phishing:                  {len(phishing)} ({len(phishing)/len(samples):.1%})")
    print(f"  Legitimate:                {len(legit)} ({len(legit)/len(samples):.1%})")

    if phishing:
        urls_phish = [len(s.urls) for s in phishing]
        chars_phish = [len(s.clean_text) for s in phishing]
        print(f"\n  Phishing — avg URLs:       {statistics.mean(urls_phish):.2f}")
        print(f"  Phishing — avg body chars: {statistics.mean(chars_phish):.0f}")

    if legit:
        urls_legit = [len(s.urls) for s in legit]
        chars_legit = [len(s.clean_text) for s in legit]
        print(f"  Legit    — avg URLs:       {statistics.mean(urls_legit):.2f}")
        print(f"  Legit    — avg body chars: {statistics.mean(chars_legit):.0f}")


def experiment_5_html_stripping():
    """Experiment 5: Prove HTML stripping works on a malicious-style HTML input."""
    print("\n=== Experiment 5: HTML Stripping ===")

    html_msg = """<html><body>
    <h1>Important Notice</h1>
    <p>Click <a href="https://fake-bank.com">here</a> to verify.</p>
    <script>alert('xss');</script>
    <style>body{color:red}</style>
    </body></html>"""

    rec = preprocess_text(html_msg)
    print(f"  Raw size:   {len(html_msg)} chars")
    print(f"  Clean size: {len(rec.clean_text)} chars (reduced by {(1-len(rec.clean_text)/len(html_msg)):.0%})")
    print(f"  Clean text: {rec.clean_text!r}")
    print(f"  URLs:       {rec.urls}")
    assert "<script>" not in rec.clean_text, "Script tag was not stripped!"
    assert "alert" not in rec.clean_text, "JS code was not stripped!"
    print(f"  [PASS] Script/style tags successfully removed")


if __name__ == "__main__":
    print("=" * 60)
    print("MEMBER 1 — DATA ENGINEER — EXPERIMENTAL RESULTS")
    print("=" * 60)

    experiment_1_url_extraction()
    experiment_2_auth_parsing()
    experiment_3_preprocess_speed()
    experiment_4_dataset_statistics()
    experiment_5_html_stripping()

    print("\n" + "=" * 60)
    print("DONE. Copy this output into your Week 14/15 report.")
    print("=" * 60)
