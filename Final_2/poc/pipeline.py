"""End-to-end orchestrator: text/file in → preprocessed → LLM → formatted result."""
from __future__ import annotations

from pathlib import Path

from data import preprocess, preprocess_text
from llm import predict


def analyze_single(text_or_path, strategy: str = "cot") -> dict:
    """
    The main UI entry point. Accepts pasted text or a file path.
    Returns a dict ready for the Gradio UI.
    """
    if isinstance(text_or_path, (str, Path)) and Path(text_or_path).exists():
        record = preprocess(Path(text_or_path))
    else:
        record = preprocess_text(str(text_or_path))

    prediction = predict(record, strategy=strategy)

    return {
        "verdict": prediction.label,
        "confidence": prediction.confidence,
        "red_flags": prediction.red_flags,
        "reasoning": prediction.reasoning,
        "latency_ms": prediction.latency_ms,
        "strategy": prediction.strategy,
        "extracted_urls": record.urls,
        "auth_status": record.auth_status,
    }
