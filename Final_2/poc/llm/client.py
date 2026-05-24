"""Gemini API client wrapper. Handles auth, retries, rate limiting, JSON parsing."""
from __future__ import annotations

import time
from typing import Optional

from .prompts import get_strategy
from .schema import Prediction, parse_llm_response
from config import (
    GEMINI_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    RETRY_MAX_ATTEMPTS, RETRY_BASE_DELAY, require_api_key,
)


_GEMINI_CONFIGURED = False


def _ensure_configured():
    """Lazy-configure Gemini SDK only when first needed."""
    global _GEMINI_CONFIGURED
    if _GEMINI_CONFIGURED:
        return
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        ) from e
    genai.configure(api_key=require_api_key())
    _GEMINI_CONFIGURED = True


def _call_gemini_once(system_prompt: str, user_prompt: str) -> str:
    """Single Gemini API call. Returns raw text."""
    import google.generativeai as genai
    _ensure_configured()

    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config={
            "temperature": LLM_TEMPERATURE,
            "max_output_tokens": LLM_MAX_TOKENS,
            "response_mime_type": "application/json",
        },
    )
    response = model.generate_content(user_prompt)
    return response.text or ""


def predict(record_or_text, strategy: str = "cot") -> Prediction:
    """
    Run a prediction. Accepts either a Record (preferred) or a raw text string.
    Returns a validated Prediction. Retries on transient errors and malformed JSON.
    """
    # Accept either a Record-like object with llm_input_text(), or a raw string
    if hasattr(record_or_text, "llm_input_text"):
        message = record_or_text.llm_input_text()
    else:
        message = str(record_or_text)

    prompt_fn = get_strategy(strategy)
    system_prompt, user_prompt = prompt_fn(message)

    last_error: Optional[Exception] = None
    start = time.time()

    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            raw = _call_gemini_once(system_prompt, user_prompt)
            prediction = parse_llm_response(raw)
            prediction.strategy = strategy
            prediction.latency_ms = int((time.time() - start) * 1000)
            return prediction
        except Exception as e:
            last_error = e
            # Don't sleep on the last attempt
            if attempt < RETRY_MAX_ATTEMPTS:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                time.sleep(delay)

    # All retries failed — return a fallback prediction so the UI never crashes
    return Prediction(
        label="suspect",
        confidence=0.0,
        red_flags=["llm_call_failed"],
        reasoning=f"The LLM call failed after {RETRY_MAX_ATTEMPTS} attempts. "
                  f"Last error: {type(last_error).__name__}: {last_error}. "
                  f"Defaulting to 'suspect' for safety.",
        strategy=strategy,
        latency_ms=int((time.time() - start) * 1000),
    )


def predict_batch(records: list, strategy: str = "cot",
                  progress_callback=None) -> list[Prediction]:
    """Run predictions sequentially. Use a callback to report progress."""
    predictions = []
    for i, rec in enumerate(records):
        pred = predict(rec, strategy=strategy)
        predictions.append(pred)
        if progress_callback:
            progress_callback(i + 1, len(records), pred)
    return predictions
