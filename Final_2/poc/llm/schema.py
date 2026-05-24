"""Strict JSON output schema for LLM predictions, plus validation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_LABELS = {"phishing", "safe", "suspect"}


@dataclass
class Prediction:
    label: str  # "phishing" | "safe" | "suspect"
    confidence: float  # 0.0 to 1.0
    red_flags: list[str] = field(default_factory=list)
    reasoning: str = ""
    strategy: Optional[str] = None
    latency_ms: Optional[int] = None
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def label_binary(self) -> int:
        """Map label to {0,1} for metric computation."""
        return 1 if self.label in ("phishing", "suspect") else 0


def _extract_json_block(text: str) -> str:
    """Strip markdown code fences and isolate the first {...} JSON object."""
    text = text.strip()
    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Find the outermost { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start:end + 1]


def parse_llm_response(raw: str) -> Prediction:
    """Parse a raw LLM response into a validated Prediction. Raises ValueError on bad input."""
    if not raw or not raw.strip():
        raise ValueError("Empty LLM response")

    json_text = _extract_json_block(raw)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Expected object, got {type(data).__name__}")

    label = str(data.get("label", "")).lower().strip()
    if label not in VALID_LABELS:
        raise ValueError(f"Invalid label: {label!r} (expected one of {VALID_LABELS})")

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        raise ValueError("confidence must be a number")
    confidence = max(0.0, min(1.0, confidence))

    red_flags = data.get("red_flags", [])
    if not isinstance(red_flags, list):
        red_flags = [str(red_flags)]
    red_flags = [str(x).strip() for x in red_flags if str(x).strip()]

    reasoning = str(data.get("reasoning", "")).strip()

    return Prediction(
        label=label,
        confidence=confidence,
        red_flags=red_flags,
        reasoning=reasoning,
        raw_response=raw,
    )
