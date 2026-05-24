"""Qualitative error analysis: sample false positives and false negatives."""
from __future__ import annotations

from typing import Iterable


def collect_errors(records, predictions, limit: int = 20) -> dict:
    """Return dict with sampled false positives, false negatives, and successes."""
    fps, fns, tps, tns = [], [], [], []
    for rec, pred in zip(records, predictions):
        if rec.label is None:
            continue
        actual = rec.label
        predicted = pred.label_binary
        entry = {
            "id": rec.id,
            "subject": rec.subject,
            "sender": rec.sender,
            "prediction": pred.to_dict(),
            "snippet": (rec.clean_text or "")[:200],
        }
        if actual == 0 and predicted == 1:
            fps.append(entry)
        elif actual == 1 and predicted == 0:
            fns.append(entry)
        elif actual == 1 and predicted == 1:
            tps.append(entry)
        else:
            tns.append(entry)

    return {
        "false_positives": fps[:limit],
        "false_negatives": fns[:limit],
        "true_positives_sample": tps[:5],
        "true_negatives_sample": tns[:5],
        "counts": {
            "fp": len(fps), "fn": len(fns),
            "tp": len(tps), "tn": len(tns),
        },
    }


def categorize_failure_modes(errors: Iterable[dict]) -> dict[str, int]:
    """Tally red-flag categories across a list of error entries — simple frequency count."""
    tally: dict[str, int] = {}
    for e in errors:
        for flag in e.get("prediction", {}).get("red_flags", []):
            tally[flag] = tally.get(flag, 0) + 1
    return dict(sorted(tally.items(), key=lambda x: -x[1]))
