"""
llm/client.py — Google Gemini API wrapper (google-genai SDK).

Public API (unchanged):
    predict(record_or_text, strategy="zero_shot") -> Prediction
    predict_batch(records, strategy, progress_callback=None) -> list[Prediction]
"""

import time
from typing import Callable, Optional

from google import genai
from google.genai import errors as genai_errors

import config
from llm.prompts import get_strategy
from llm.schema import parse_llm_response, Prediction
from data.preprocessor import Record

# ---------------------------------------------------------------------------
# Rate-limit throttle  (60 RPM → 1 second between calls)
# ---------------------------------------------------------------------------

_MIN_CALL_INTERVAL: float = 60.0 / config.GEMINI_RPM   # = 1.0 s
_last_call_ts: float = 0.0


def _throttle() -> None:
    global _last_call_ts
    elapsed = time.monotonic() - _last_call_ts
    gap = _MIN_CALL_INTERVAL - elapsed
    if gap > 0:
        time.sleep(gap)
    _last_call_ts = time.monotonic()


# ---------------------------------------------------------------------------
# API client factory
# ---------------------------------------------------------------------------

def _make_client() -> genai.Client:
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Set it with: $env:GEMINI_API_KEY='...' (PowerShell) "
            "or export GEMINI_API_KEY='...' (bash)."
        )
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Single API call
# ---------------------------------------------------------------------------

def _call_gemini_once(client: genai.Client, system_prompt: str, user_prompt: str) -> str:
    response = client.models.generate_content(
        model=config.LLM_MODEL,
        contents=user_prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=config.LLM_TEMPERATURE,
            max_output_tokens=config.LLM_MAX_TOKENS,
            response_mime_type="application/json",
        ),
    )
    return response.text or ""



# ---------------------------------------------------------------------------
# Fallback sentinel
# ---------------------------------------------------------------------------

def _fallback(reason: str) -> Prediction:
    return Prediction(
        label="suspect",
        confidence=0.0,
        red_flags=["llm_call_failed"],
        reasoning=f"llm_call_failed: {reason}",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict(record_or_text: "Record | str", strategy: str = "zero_shot") -> Prediction:
    """Run a single prediction.  Retries up to RETRY_MAX_ATTEMPTS on transient errors."""
    if isinstance(record_or_text, str):
        from data.preprocessor import preprocess_text
        record = preprocess_text(record_or_text)
    else:
        record = record_or_text

    prompt_fn = get_strategy(strategy)
    system_prompt, user_prompt = prompt_fn(record.llm_input_text())

    client = _make_client()
    last_error: Optional[Exception] = None
    start = time.monotonic()

    for attempt in range(config.RETRY_MAX_ATTEMPTS):
        try:
            _throttle()
            raw = _call_gemini_once(client, system_prompt, user_prompt)
            prediction = parse_llm_response(raw)
            prediction.strategy = strategy
            prediction.latency_ms = int((time.monotonic() - start) * 1000)
            return prediction

        except genai_errors.APIError as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            last_error = exc
            if status == 429:
                # Rate limited — wait a full minute before retrying
                time.sleep(60.0)
            elif status == 503:
                # Temporary overload — exponential backoff
                backoff = config.RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(backoff)
            else:
                backoff = config.RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(backoff)

        except ValueError as exc:
            last_error = exc
            backoff = config.RETRY_BASE_DELAY * (2 ** attempt)
            time.sleep(backoff)

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(config.RETRY_BASE_DELAY)

    return _fallback(str(last_error))


def predict_batch(
    records: list,
    strategy: str = "zero_shot",
    progress_callback: Optional[Callable] = None,
) -> list:
    """Run predict() sequentially over a list of Records.

    progress_callback, if provided, is called as callback(idx, total, pred)
    after each prediction — matching the signature expected by eval/harness.py.
    """
    results = []
    total = len(records)
    for idx, record in enumerate(records, start=1):
        pred = predict(record, strategy=strategy)
        results.append(pred)
        if progress_callback:
            progress_callback(idx, total, pred)
    return results
