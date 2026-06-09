"""
Evaluation runner: runs all three prompt strategies on the full test set,
captures verbose output, computes avg latency, and writes:
  - results/evaluation_results_week15.txt   (full terminal output)
  - results/evaluation_summary_week15.md    (clean summary table)
"""
from __future__ import annotations

import io
import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

# Make sure the project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.preprocessor import preprocess_text
from eval.harness import evaluate
from eval.metrics import format_report

RESULTS_DIR = ROOT / "results"
TEST_SET = ROOT / "data" / "samples" / "kaggle_dataset_v2.json"
OUTPUT_TXT = RESULTS_DIR / "evaluation_results_week15.txt"
SUMMARY_MD = RESULTS_DIR / "evaluation_summary_week15.md"
STRATEGIES = ["zero_shot", "few_shot", "cot"]


def load_records():
    print(f"Loading test set: {TEST_SET}")
    with open(TEST_SET, encoding="utf-8") as f:
        data = json.load(f)
    records = [preprocess_text(item["text"], label=item.get("label")) for item in data]
    labeled = [r for r in records if r.label is not None]
    print(f"Loaded {len(labeled)} labeled records (of {len(records)} total).\n")
    return labeled


def run_all(records):
    all_results = {}
    for strat in STRATEGIES:
        print(f"\n{'='*60}")
        print(f"Running strategy: {strat}")
        print(f"{'='*60}")
        t0 = time.time()
        metrics, predictions = evaluate(records, strategy=strat, verbose=True)
        wall_time = time.time() - t0
        avg_latency = (
            sum(p.latency_ms for p in predictions if p.latency_ms is not None)
            / max(1, sum(1 for p in predictions if p.latency_ms is not None))
        )
        print(format_report(metrics, title=f"Strategy: {strat}"))
        print(f"Wall-clock time: {wall_time:.1f}s  |  Avg latency/call: {avg_latency:.0f}ms")
        all_results[strat] = {
            "metrics": metrics,
            "avg_latency_ms": avg_latency,
        }
    return all_results


def build_summary_table(all_results: dict) -> str:
    header = (
        "| Strategy   | Accuracy | Precision | Recall   | F1       | Failure Rate | Avg Latency (ms) |\n"
        "|------------|----------|-----------|----------|----------|--------------|------------------|\n"
    )
    rows = []
    for strat, res in all_results.items():
        m = res["metrics"]
        lat = res["avg_latency_ms"]
        rows.append(
            f"| {strat:<10} | {m.accuracy:.4f}   | {m.precision:.4f}    | "
            f"{m.recall:.4f}   | {m.f1:.4f}   | {m.failure_rate:.4f}       | {lat:>16.0f} |"
        )
    return header + "\n".join(rows) + "\n"


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    # Capture all stdout into buffer AND print to terminal simultaneously
    full_log = io.StringIO()

    class Tee(io.TextIOBase):
        def __init__(self, *targets):
            self.targets = targets
        def write(self, s):
            for t in self.targets:
                t.write(s)
            return len(s)
        def flush(self):
            for t in self.targets:
                t.flush()

    tee = Tee(sys.stdout, full_log)

    banner = (
        "=" * 60 + "\n"
        "LLM Phishing Detector — Full Evaluation (Week 15)\n"
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "=" * 60 + "\n"
    )

    with redirect_stdout(tee):
        print(banner)
        records = load_records()
        all_results = run_all(records)

        print("\n\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        for strat, res in all_results.items():
            m = res["metrics"]
            lat = res["avg_latency_ms"]
            print(
                f"  {strat:<12}  accuracy={m.accuracy:.4f}  "
                f"precision={m.precision:.4f}  recall={m.recall:.4f}  "
                f"F1={m.f1:.4f}  failure_rate={m.failure_rate:.4f}  "
                f"avg_latency={lat:.0f}ms"
            )

    # --- Save full log ---
    log_text = full_log.getvalue()
    OUTPUT_TXT.write_text(log_text, encoding="utf-8")
    print(f"\n✓ Full output saved to: {OUTPUT_TXT}")

    # --- Build and save summary markdown ---
    table = build_summary_table(all_results)
    md_content = (
        "# Evaluation Summary — Week 15\n\n"
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n"
        f"**Test set:** `{TEST_SET.name}` ({len(records)} labeled samples)  \n"
        f"**Strategies evaluated:** {', '.join(STRATEGIES)}\n\n"
        "## Results\n\n"
        + table +
        "\n> Precision, Recall, and F1 are computed for the **phishing (positive)** class.\n"
        "> Failure Rate = fraction of samples where the LLM call failed after all retries.\n"
    )
    SUMMARY_MD.write_text(md_content, encoding="utf-8")
    print(f"✓ Summary table saved to: {SUMMARY_MD}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
