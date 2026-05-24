"""
LLM Client Module (Owner: Member 2)
Wrapper around Gemini API with retry logic, rate limiting, and JSON validation.
"""
import json
import os
import time
from typing import Literal

import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError

from .prompts import build_prompt


class PhishingResult(BaseModel):
    label: Literal["phishing", "safe", "suspect"]
    confidence: float = Field(ge=0.0, le=1.0)
    red_flags: list[str]
    reasoning: dict | None = None


class LLMClient:
    """Client for Gemini-powered phishing analysis."""

    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: str | None = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Set env var or pass api_key=...")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.retry_count = 3
        self.last_call_ts = 0.0
        self.min_interval = 4.0  # ~15 req/min for free tier

    def analyze(self, preprocessed: dict, strategy: str = "cot") -> dict:
        """
        Analyze a preprocessed message.
        Input: dict from preprocessing.process()
        Output: dict matching PhishingResult schema + processing_time_ms.
        """
        message = preprocessed.get("cleaned_text", preprocessed.get("raw_content", ""))
        prompt = build_prompt(message, strategy)

        self._respect_rate_limit()
        start = time.time()
        raw_response = self._call_with_retry(prompt)
        latency_ms = int((time.time() - start) * 1000)

        result = self._parse_response(raw_response)
        result["processing_time_ms"] = latency_ms
        result["strategy"] = strategy
        return result

    def _respect_rate_limit(self):
        elapsed = time.time() - self.last_call_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_ts = time.time()

    def _call_with_retry(self, prompt: str) -> str:
        for attempt in range(self.retry_count):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.0,
                        "response_mime_type": "application/json",
                    },
                )
                return response.text
            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise
                wait = 2 ** attempt
                print(f"[LLMClient] Retry {attempt + 1} after error: {e}. Wait {wait}s.")
                time.sleep(wait)

    def _parse_response(self, raw: str) -> dict:
        """Parse + validate JSON response, with fallback."""
        # Strip markdown wrappers if present
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
            validated = PhishingResult(**parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"[LLMClient] Parse error: {e}. Falling back to 'suspect'.")
            return {
                "label": "suspect",
                "confidence": 0.5,
                "red_flags": ["LLM response parsing failed"],
                "reasoning": {"error": str(e), "raw": raw[:500]},
            }
