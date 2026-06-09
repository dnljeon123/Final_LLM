"""
Disk-backed preprocessing cache.
Implements Week 15 plan item: caching layer to avoid re-preprocessing.

Usage:
    from data.cache import cached_preprocess
    record = cached_preprocess(raw_text, label=1)

The cache key includes a preprocessor version string, so cached records
become stale automatically if the preprocessor changes.
"""
from __future__ import annotations

import hashlib
import pickle
import time
from pathlib import Path
from typing import Optional

from config import CACHE_DIR as _CONFIG_CACHE_DIR
from .preprocessor import preprocess_text, Record


CACHE_DIR = _CONFIG_CACHE_DIR / "preprocess"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Bump this when preprocessor logic changes — invalidates the cache
PREPROCESSOR_VERSION = "v2"


def _cache_key(text: str) -> str:
    """Deterministic cache key combining content hash + preprocessor version."""
    content_hash = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{PREPROCESSOR_VERSION}_{content_hash}"


def cached_preprocess(text: str, label: Optional[int] = None) -> Record:
    """Preprocess with disk cache. Returns the cached Record if available."""
    key = _cache_key(text)
    cache_path = CACHE_DIR / f"{key}.pkl"

    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                cached = pickle.load(f)
            cached.label = label  # label may differ from cached entry
            return cached
        except (pickle.PickleError, EOFError):
            cache_path.unlink(missing_ok=True)  # corrupt cache, regenerate

    record = preprocess_text(text, label=label)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(record, f)
    except OSError:
        pass  # cache write failed, ignore — return uncached record
    return record


def clear_cache():
    """Remove all cached preprocessed records."""
    n = 0
    for path in CACHE_DIR.glob("*.pkl"):
        path.unlink()
        n += 1
    return n


def cache_stats() -> dict:
    """Return statistics about the current cache."""
    files = list(CACHE_DIR.glob("*.pkl"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "entries": len(files),
        "total_bytes": total_size,
        "version": PREPROCESSOR_VERSION,
        "dir": str(CACHE_DIR),
    }


def benchmark_cache(texts: list[str], labels: list[int]) -> dict:
    """Compare cold vs warm preprocessing speed."""
    clear_cache()

    # Cold run
    start = time.perf_counter()
    for text, label in zip(texts, labels):
        cached_preprocess(text, label=label)
    cold_time = time.perf_counter() - start

    # Warm run
    start = time.perf_counter()
    for text, label in zip(texts, labels):
        cached_preprocess(text, label=label)
    warm_time = time.perf_counter() - start

    return {
        "n_samples": len(texts),
        "cold_seconds": round(cold_time, 3),
        "warm_seconds": round(warm_time, 3),
        "speedup_x": round(cold_time / max(warm_time, 0.0001), 1),
    }
