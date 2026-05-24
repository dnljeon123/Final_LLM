"""Dataset loaders. Real datasets must be downloaded separately (see README)."""
from __future__ import annotations

import json
import random
from pathlib import Path

from .preprocessor import Record, preprocess, preprocess_text
from config import SAMPLES_DIR, TEST_SPLIT_SEED, TEST_SPLIT_RATIO


def load_samples() -> list[Record]:
    """Load the bundled demo samples (6 messages: 3 phishing + 3 legitimate)."""
    samples_file = SAMPLES_DIR / "demo_samples.json"
    if not samples_file.exists():
        return []
    with open(samples_file, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for item in data:
        rec = preprocess_text(item["text"], label=item.get("label"))
        rec.metadata["sample_name"] = item.get("name", "")
        out.append(rec)
    return out


def load_eml_directory(directory: Path, label: int) -> list[Record]:
    """Load every .eml file in a directory with the given label."""
    records = []
    for path in Path(directory).glob("*.eml"):
        try:
            records.append(preprocess(path, label=label))
        except Exception as e:
            print(f"[WARN] failed to parse {path.name}: {e}")
    return records


def stratified_split(records: list[Record], ratio: float = TEST_SPLIT_RATIO,
                     seed: int = TEST_SPLIT_SEED) -> tuple[list[Record], list[Record]]:
    """Stratified train/test split by label."""
    rng = random.Random(seed)
    by_label: dict[int | None, list[Record]] = {}
    for r in records:
        by_label.setdefault(r.label, []).append(r)
    train, test = [], []
    for label, group in by_label.items():
        rng.shuffle(group)
        n_test = int(len(group) * ratio)
        test.extend(group[:n_test])
        train.extend(group[n_test:])
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test
