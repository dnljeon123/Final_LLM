"""
Evaluation Metrics Module (Owner: Member 3)
Compute classification metrics + visualizations.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    fbeta_score,
    precision_score,
    recall_score,
)


def compute_metrics(y_true: list[str], y_pred: list[str], pos_label: str = "phishing") -> dict:
    """
    Compute classification metrics for phishing detection.

    Converts 3-class (phishing/safe/suspect) → binary by treating suspect as phishing
    (security-conservative: false alarm better than miss).
    """
    # Binarize: suspect -> phishing
    y_true_bin = ["phishing" if y == "phishing" else "safe" for y in y_true]
    y_pred_bin = ["phishing" if y in ("phishing", "suspect") else "safe" for y in y_pred]

    return {
        "accuracy": round(accuracy_score(y_true_bin, y_pred_bin), 4),
        "precision": round(precision_score(y_true_bin, y_pred_bin, pos_label=pos_label, zero_division=0), 4),
        "recall": round(recall_score(y_true_bin, y_pred_bin, pos_label=pos_label, zero_division=0), 4),
        "f1": round(fbeta_score(y_true_bin, y_pred_bin, beta=1, pos_label=pos_label, zero_division=0), 4),
        "f2": round(fbeta_score(y_true_bin, y_pred_bin, beta=2, pos_label=pos_label, zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_true_bin, y_pred_bin, labels=["phishing", "safe"]).tolist(),
        "n_samples": len(y_true),
    }


def expected_calibration_error(confidences: list[float], correct: list[bool], n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE).
    Lower = better calibrated. ECE=0 means confidence matches accuracy perfectly.
    """
    confidences = np.array(confidences)
    correct = np.array(correct, dtype=float)
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (confidences > bin_edges[i]) & (confidences <= bin_edges[i + 1])
        if mask.sum() > 0:
            avg_conf = confidences[mask].mean()
            avg_acc = correct[mask].mean()
            weight = mask.sum() / len(confidences)
            ece += weight * abs(avg_conf - avg_acc)
    return round(float(ece), 4)


def compare_strategies(results_per_strategy: dict[str, dict]) -> str:
    """Generate human-readable comparison table."""
    lines = ["| Strategy | Accuracy | Precision | Recall | F1 | F2 |", "|----------|----------|-----------|--------|-----|-----|"]
    for strat, m in results_per_strategy.items():
        lines.append(
            f"| {strat} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
            f"{m['recall']:.3f} | {m['f1']:.3f} | {m['f2']:.3f} |"
        )
    return "\n".join(lines)


def save_results(results: dict, output_path: str = "evaluation_results.json"):
    """Persist results for UI consumption."""
    Path(output_path).write_text(json.dumps(results, indent=2))
