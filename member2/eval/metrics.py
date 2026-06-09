"""Metric computation: Accuracy, Precision, Recall, F1, confusion matrix."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Metrics:
    accuracy: float
    precision: float  # phishing class
    recall: float     # phishing class
    f1: float         # phishing class
    tp: int
    fp: int
    tn: int
    fn: int
    total: int
    failure_rate: float = 0.0  # fraction of records where LLM call failed

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision_phishing": round(self.precision, 4),
            "recall_phishing": round(self.recall, 4),
            "f1_phishing": round(self.f1, 4),
            "confusion_matrix": {"tp": self.tp, "fp": self.fp, "tn": self.tn, "fn": self.fn},
            "total": self.total,
            "failure_rate": round(self.failure_rate, 4),
        }


def compute_metrics(y_true: list[int], y_pred: list[int], failures: int = 0) -> Metrics:
    """
    Compute classification metrics for binary phishing detection.
    Convention: 1 = phishing (positive class), 0 = legitimate.
    """
    assert len(y_true) == len(y_pred), "y_true and y_pred must have the same length"
    if not y_true:
        return Metrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    total = len(y_true)

    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    failure_rate = failures / (total + failures) if (total + failures) else 0.0

    return Metrics(
        accuracy=accuracy, precision=precision, recall=recall, f1=f1,
        tp=tp, fp=fp, tn=tn, fn=fn, total=total, failure_rate=failure_rate,
    )


def format_report(metrics: Metrics, title: str = "Evaluation Report") -> str:
    m = metrics
    return (
        f"\n=== {title} ===\n"
        f"Total samples:    {m.total}\n"
        f"Accuracy:         {m.accuracy:.4f}\n"
        f"Precision (P):    {m.precision:.4f}\n"
        f"Recall (P):       {m.recall:.4f}\n"
        f"F1 (P):           {m.f1:.4f}\n"
        f"Failure rate:     {m.failure_rate:.4f}\n"
        f"\nConfusion Matrix:\n"
        f"                Predicted\n"
        f"                Phish   Safe\n"
        f"  Actual Phish  {m.tp:5d}  {m.fn:5d}\n"
        f"         Safe   {m.fp:5d}  {m.tn:5d}\n"
    )
