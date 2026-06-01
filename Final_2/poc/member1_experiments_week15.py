"""
Member 1 — Week 15 experiments script.
Runs all experiments needed for the Week 15 report on the SCALED dataset.

Usage:
    python member1_experiments_week15.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

from data.preprocessor import preprocess_text
from data.cache import cached_preprocess, clear_cache, cache_stats, benchmark_cache


SCALED_JSON = Path("data/samples/kaggle_dataset_v2.json")


def load_records():
    """Load the Week 15 scaled dataset."""
    if not SCALED_JSON.exists():
        print(f"ERROR: {SCALED_JSON} not found.")
        print("Run `python convert_kaggle_dataset_v2.py` first.")
        return [], []

    with open(SCALED_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    records = [preprocess_text(item["text"], label=item.get("label")) for item in raw]
    texts = [item["text"] for item in raw]
    labels = [item["label"] for item in raw]
    return records, texts, labels


def experiment_1_scale_comparison(records):
    """Compare scaled dataset (Week 15) vs original (Week 14)."""
    print("\n=== Experiment 1: Scale Comparison (Week 14 vs Week 15) ===")

    phishing = [r for r in records if r.label == 1]
    legit = [r for r in records if r.label == 0]

    print(f"  Week 14 corpus:           200 samples (100/100)")
    print(f"  Week 15 corpus:           {len(records)} samples ({len(phishing)}/{len(legit)})")
    print(f"  Scale factor:             {len(records) / 200:.1f}x")


def experiment_2_url_fix_validation(records):
    """Validate the URL=0 fix from Week 14 — adding synthetic GitHub/Stripe legit."""
    print("\n=== Experiment 2: URL Coverage After Synthetic Legit Augmentation ===")

    phishing = [r for r in records if r.label == 1]
    legit = [r for r in records if r.label == 0]

    p_with_url = sum(1 for r in phishing if r.urls)
    l_with_url = sum(1 for r in legit if r.urls)

    print(f"  Phishing emails with URLs:    {p_with_url} / {len(phishing)} "
          f"({p_with_url / len(phishing):.1%})")
    print(f"  Legit emails with URLs:       {l_with_url} / {len(legit)} "
          f"({l_with_url / len(legit):.1%})")
    print(f"  Week 14 legit URL rate:       0.0% (Enron only)")
    print(f"  Week 15 legit URL rate:       {l_with_url / len(legit):.1%} (Enron + synthetic)")
    print(f"  -> Baseline more realistic; URL is still strong but not perfect signal")


def experiment_3_cache_benchmark(texts, labels):
    """Measure speedup from disk-backed caching."""
    print("\n=== Experiment 3: Disk Cache Benchmark ===")

    # Use first 200 samples for the benchmark (matches Week 14 size)
    sample_texts = texts[:200]
    sample_labels = labels[:200]

    result = benchmark_cache(sample_texts, sample_labels)
    print(f"  Samples:                  {result['n_samples']}")
    print(f"  Cold preprocessing time:  {result['cold_seconds']} s")
    print(f"  Warm (cached) time:       {result['warm_seconds']} s")
    print(f"  Speedup from cache:       {result['speedup_x']}x")

    stats = cache_stats()
    print(f"  Cache entries on disk:    {stats['entries']}")
    print(f"  Cache size:               {stats['total_bytes'] / 1024:.1f} KB")


def experiment_4_throughput_at_scale(records):
    """Measure preprocessing throughput on the full Week 15 corpus."""
    print("\n=== Experiment 4: Throughput at Week 15 Scale ===")

    times = []
    for r in records:
        start = time.perf_counter()
        _ = preprocess_text(r.raw_text, label=r.label)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    total_s = sum(times) / 1000
    throughput = len(times) / total_s if total_s > 0 else 0

    print(f"  Samples processed:        {len(times)}")
    print(f"  Total time:               {total_s:.2f} s")
    print(f"  Mean latency:             {statistics.mean(times):.3f} ms")
    print(f"  p50 latency:              {statistics.median(times):.3f} ms")
    print(f"  p95 latency:              {sorted(times)[int(len(times) * 0.95)]:.3f} ms")
    print(f"  Throughput:               {throughput:.0f} emails/second")


def experiment_5_length_at_scale(records):
    """Confirm Week 14 length finding holds at Week 15 scale."""
    print("\n=== Experiment 5: Length Statistics at Scale ===")

    p_lengths = [len(r.clean_text) for r in records if r.label == 1]
    l_lengths = [len(r.clean_text) for r in records if r.label == 0]

    print(f"  Phishing — median length: {statistics.median(p_lengths):8.0f} chars "
          f"(Week 14: 2,192)")
    print(f"  Legit    — median length: {statistics.median(l_lengths):8.0f} chars "
          f"(Week 14: 784)")
    ratio = statistics.median(p_lengths) / max(statistics.median(l_lengths), 1)
    print(f"  Length ratio:             {ratio:.2f}x  (Week 14: 2.8x)")


def experiment_6_edge_case_summary():
    """Report results from the edge-case unit tests."""
    print("\n=== Experiment 6: Edge-Case Test Suite ===")

    import subprocess
    test_file = Path("tests/test_edge_cases.py")
    if not test_file.exists():
        print(f"  [WARN] {test_file} not found. Skipping.")
        return

    print(f"  Running: pytest {test_file} ...")
    result = subprocess.run(
        ["pytest", str(test_file), "-q", "--tb=no"],
        capture_output=True, text=True,
    )
    # Print last 3 lines (pytest summary)
    for line in result.stdout.strip().splitlines()[-3:]:
        print(f"  {line}")


if __name__ == "__main__":
    print("=" * 60)
    print("MEMBER 1 — WEEK 15 EXPERIMENTS (Scaled Dataset)")
    print("=" * 60)

    records, texts, labels = load_records()
    if not records:
        sys.exit(1)

    experiment_1_scale_comparison(records)
    experiment_2_url_fix_validation(records)
    experiment_3_cache_benchmark(texts, labels)
    experiment_4_throughput_at_scale(records)
    experiment_5_length_at_scale(records)
    experiment_6_edge_case_summary()

    print("\n" + "=" * 60)
    print("DONE. These numbers are REAL — paste them into Week 15 report.")
    print("=" * 60)
