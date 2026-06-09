"""Evaluation harness — runs strategies on labeled test sets and reports metrics."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python -m eval.harness` or `python eval/harness.py`
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data import load_samples, stratified_split
from llm import predict_batch
from llm.prompts import STRATEGIES
from .metrics import compute_metrics, format_report, Metrics


def _progress(i, n, pred):
    print(f"  [{i}/{n}] verdict={pred.label} conf={pred.confidence:.2f} "
          f"latency={pred.latency_ms}ms", flush=True)


def evaluate(records, strategy: str = "cot", verbose: bool = True) -> tuple[Metrics, list]:
    """Run a strategy across labeled records, return (metrics, predictions)."""
    labeled = [r for r in records if r.label is not None]
    if not labeled:
        raise ValueError("No labeled records to evaluate")

    if verbose:
        print(f"\nRunning strategy={strategy} on {len(labeled)} records...")
    predictions = predict_batch(
        labeled, strategy=strategy,
        progress_callback=_progress if verbose else None,
    )

    y_true = [r.label for r in labeled]
    y_pred = [p.label_binary for p in predictions]
    failures = sum(1 for p in predictions if "llm_call_failed" in p.red_flags)
    # Failures stay in the prediction list but we report rate separately
    metrics = compute_metrics(y_true, y_pred, failures=failures)
    return metrics, predictions


def main():
    parser = argparse.ArgumentParser(description="Phishing detector evaluation harness")
    parser.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="cot",
                        help="Which prompt strategy to evaluate (default: cot)")
    parser.add_argument("--compare-all", action="store_true",
                        help="Run all three strategies and compare")
    parser.add_argument("--test-set", type=Path, default=None,
                        help="Path to a test set JSON (defaults to bundled samples)")
    args = parser.parse_args()

    # Load test data
    if args.test_set and args.test_set.exists():
        # Custom test set: same format as demo_samples.json
        from data.preprocessor import preprocess_text
        with open(args.test_set, encoding="utf-8") as f:
            data = json.load(f)
        records = [preprocess_text(item["text"], label=item.get("label")) for item in data]
    else:
        print("Using bundled demo samples (6 messages). For real evaluation, pass --test-set.")
        records = load_samples()

    if not records:
        print("ERROR: no records loaded.")
        return 1

    if args.compare_all:
        results = {}
        for strat in ["zero_shot", "few_shot", "cot"]:
            metrics, _ = evaluate(records, strategy=strat, verbose=True)
            results[strat] = metrics.to_dict()
            print(format_report(metrics, title=f"Strategy: {strat}"))
        print("\n=== COMPARISON SUMMARY ===")
        for strat, m in results.items():
            print(f"  {strat:15s} accuracy={m['accuracy']:.3f}  "
                  f"F1={m['f1_phishing']:.3f}")
    else:
        metrics, _ = evaluate(records, strategy=args.strategy, verbose=True)
        print(format_report(metrics, title=f"Strategy: {args.strategy}"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
