"""
Member 1 — Experiments on the REAL Kaggle dataset (200 samples).
Run this AFTER running convert_kaggle_dataset.py first.

Usage:
    python member1_experiments_v2.py
"""
import json
import statistics
import time
from pathlib import Path

from data.preprocessor import preprocess_text


KAGGLE_JSON = Path("data/samples/kaggle_dataset.json")


def load_kaggle_records():
    """Load and preprocess the 200-sample Kaggle dataset."""
    if not KAGGLE_JSON.exists():
        print(f"ERROR: {KAGGLE_JSON} not found.")
        print("Run `python convert_kaggle_dataset.py` first.")
        return []

    with open(KAGGLE_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    records = [preprocess_text(item["text"], label=item.get("label")) for item in raw]
    return records


def experiment_1_scale_stats(records):
    """Experiment 1: Dataset composition and size statistics."""
    print("\n=== Experiment 1: Dataset Composition (Real Data) ===")

    phishing = [r for r in records if r.label == 1]
    legit = [r for r in records if r.label == 0]

    print(f"  Total samples:             {len(records)}")
    print(f"  Phishing class:            {len(phishing)} ({len(phishing)/len(records):.1%})")
    print(f"  Legitimate class:          {len(legit)} ({len(legit)/len(records):.1%})")


def experiment_2_text_length(records):
    """Experiment 2: Text length comparison between phishing and legit."""
    print("\n=== Experiment 2: Text Length Analysis ===")

    phishing = [r for r in records if r.label == 1]
    legit = [r for r in records if r.label == 0]

    p_lengths = [len(r.clean_text) for r in phishing]
    l_lengths = [len(r.clean_text) for r in legit]

    print(f"  Phishing — mean length:    {statistics.mean(p_lengths):8.0f} chars")
    print(f"  Phishing — median length:  {statistics.median(p_lengths):8.0f} chars")
    print(f"  Phishing — min / max:      {min(p_lengths):4d} / {max(p_lengths)} chars")

    print(f"  Legit    — mean length:    {statistics.mean(l_lengths):8.0f} chars")
    print(f"  Legit    — median length:  {statistics.median(l_lengths):8.0f} chars")
    print(f"  Legit    — min / max:      {min(l_lengths):4d} / {max(l_lengths)} chars")


def experiment_3_url_density(records):
    """Experiment 3: URL density per class — important phishing signal."""
    print("\n=== Experiment 3: URL Density Per Class ===")

    phishing = [r for r in records if r.label == 1]
    legit = [r for r in records if r.label == 0]

    p_urls = [len(r.urls) for r in phishing]
    l_urls = [len(r.urls) for r in legit]

    print(f"  Phishing — mean URLs:      {statistics.mean(p_urls):.2f}")
    print(f"  Phishing — max URLs:       {max(p_urls)}")
    print(f"  Phishing — emails w/ URLs: {sum(1 for n in p_urls if n > 0)} / {len(p_urls)}")

    print(f"  Legit    — mean URLs:      {statistics.mean(l_urls):.2f}")
    print(f"  Legit    — max URLs:       {max(l_urls)}")
    print(f"  Legit    — emails w/ URLs: {sum(1 for n in l_urls if n > 0)} / {len(l_urls)}")

    # Compute the ratio — this is a strong "feature for phishing detection" finding
    ratio = statistics.mean(p_urls) / max(statistics.mean(l_urls), 0.01)
    print(f"\n  Phishing/Legit URL ratio:  {ratio:.2f}x")
    print(f"  (Higher ratio = URLs are a strong phishing signal)")


def experiment_4_preprocessing_speed(records):
    """Experiment 4: Preprocessing speed at scale."""
    print("\n=== Experiment 4: Preprocessing Speed at Scale ===")

    times = []
    for r in records:
        start = time.perf_counter()
        _ = preprocess_text(r.raw_text, label=r.label)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    print(f"  Samples processed:         {len(times)}")
    print(f"  Mean latency:              {statistics.mean(times):.2f} ms")
    print(f"  Median latency:            {statistics.median(times):.2f} ms")
    print(f"  Max latency:               {max(times):.2f} ms")
    print(f"  Total time:                {sum(times)/1000:.2f} seconds")
    print(f"  Throughput:                {len(times)/(sum(times)/1000):.0f} emails/second")


def experiment_5_text_reduction(records):
    """Experiment 5: How much does preprocessing reduce text size?"""
    print("\n=== Experiment 5: Preprocessing Size Reduction ===")

    raw_sizes = [len(r.raw_text) for r in records]
    clean_sizes = [len(r.clean_text) for r in records]

    total_raw = sum(raw_sizes)
    total_clean = sum(clean_sizes)
    reduction = 1 - (total_clean / total_raw) if total_raw else 0

    print(f"  Total raw chars:           {total_raw:,}")
    print(f"  Total clean chars:         {total_clean:,}")
    print(f"  Average reduction:         {reduction:.1%}")
    print(f"  Mean raw size per email:   {statistics.mean(raw_sizes):.0f} chars")
    print(f"  Mean clean size per email: {statistics.mean(clean_sizes):.0f} chars")


if __name__ == "__main__":
    print("=" * 60)
    print("MEMBER 1 — EXPERIMENTS ON REAL KAGGLE DATASET")
    print("=" * 60)

    records = load_kaggle_records()
    if not records:
        exit(1)

    experiment_1_scale_stats(records)
    experiment_2_text_length(records)
    experiment_3_url_density(records)
    experiment_4_preprocessing_speed(records)
    experiment_5_text_reduction(records)

    print("\n" + "=" * 60)
    print("DONE. These numbers are REAL — paste them into Week 14/15 report.")
    print("=" * 60)
