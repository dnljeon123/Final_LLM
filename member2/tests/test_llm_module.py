"""
Comprehensive unit tests for the llm/ module.

Covers:
  - llm/schema.py  → parse_llm_response()          (cases 1–9)
  - llm/prompts.py → prompt functions + get_strategy (cases 10–14)
  - llm/client.py  → predict() fallback behavior    (case 15)

No real API calls are made — llm.client._call_gemini_once is mocked
wherever the network would otherwise be hit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on sys.path when run directly or via pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.schema import Prediction, parse_llm_response
from llm.prompts import (
    zero_shot_prompt,
    few_shot_prompt,
    chain_of_thought_prompt,
    get_strategy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_raw(label="phishing", confidence=0.9, red_flags=None, reasoning="Test.") -> str:
    """Build a minimal valid JSON response string."""
    return json.dumps({
        "label": label,
        "confidence": confidence,
        "red_flags": red_flags if red_flags is not None else ["urgency_language"],
        "reasoning": reasoning,
    })


# ===========================================================================
# llm/schema.py — parse_llm_response()
# ===========================================================================

class TestParseValidJson:
    """Case 1: Valid JSON string → correct Prediction object."""

    def test_returns_prediction_instance(self):
        pred = parse_llm_response(_make_raw())
        assert isinstance(pred, Prediction)

    def test_label_parsed(self):
        pred = parse_llm_response(_make_raw(label="phishing"))
        assert pred.label == "phishing"

    def test_confidence_parsed(self):
        pred = parse_llm_response(_make_raw(confidence=0.77))
        assert pred.confidence == pytest.approx(0.77)

    def test_red_flags_parsed(self):
        pred = parse_llm_response(_make_raw(red_flags=["lookalike_domain", "urgency_language"]))
        assert pred.red_flags == ["lookalike_domain", "urgency_language"]

    def test_reasoning_parsed(self):
        pred = parse_llm_response(_make_raw(reasoning="Clearly malicious."))
        assert pred.reasoning == "Clearly malicious."

    def test_label_binary_phishing(self):
        pred = parse_llm_response(_make_raw(label="phishing"))
        assert pred.label_binary == 1

    def test_label_binary_suspect(self):
        pred = parse_llm_response(_make_raw(label="suspect"))
        assert pred.label_binary == 1

    def test_label_binary_safe(self):
        pred = parse_llm_response(_make_raw(label="safe"))
        assert pred.label_binary == 0


class TestMarkdownFences:
    """Case 2: JSON wrapped in markdown fences → parses correctly."""

    def test_json_fenced_block(self):
        raw = '```json\n' + _make_raw(label="safe", confidence=0.95) + '\n```'
        pred = parse_llm_response(raw)
        assert pred.label == "safe"
        assert pred.confidence == pytest.approx(0.95)

    def test_plain_fenced_block(self):
        raw = '```\n' + _make_raw(label="phishing") + '\n```'
        pred = parse_llm_response(raw)
        assert pred.label == "phishing"

    def test_fences_with_surrounding_whitespace(self):
        raw = '  ```json\n' + _make_raw(label="suspect") + '\n```  '
        pred = parse_llm_response(raw)
        assert pred.label == "suspect"


class TestMissingLabel:
    """Case 3: Missing "label" field → raises ValueError."""

    def test_missing_label_raises(self):
        raw = json.dumps({"confidence": 0.8, "red_flags": [], "reasoning": "x"})
        with pytest.raises(ValueError, match="label"):
            parse_llm_response(raw)

    def test_empty_label_raises(self):
        raw = json.dumps({"label": "", "confidence": 0.8, "red_flags": [], "reasoning": "x"})
        with pytest.raises(ValueError):
            parse_llm_response(raw)


class TestMissingRedFlags:
    """Case 4: Missing "red_flags" field → defaults to empty list (not an error).

    The schema.py implementation defaults red_flags to [] when absent,
    so this should NOT raise — it should parse gracefully.
    """

    def test_missing_red_flags_defaults_to_empty(self):
        raw = json.dumps({"label": "safe", "confidence": 0.9, "reasoning": "ok"})
        pred = parse_llm_response(raw)
        assert pred.red_flags == []

    def test_null_red_flags_coerced(self):
        # If red_flags is not a list, schema.py wraps it
        raw = json.dumps({"label": "safe", "confidence": 0.5, "red_flags": None, "reasoning": "ok"})
        pred = parse_llm_response(raw)
        assert isinstance(pred.red_flags, list)


class TestConfidenceClamping:
    """Cases 5–6: Out-of-range confidence is clamped, not rejected."""

    def test_confidence_above_one_clamped_to_one(self):
        """Case 5: confidence=1.5 → clamped to 1.0."""
        raw = _make_raw(confidence=1.5)
        pred = parse_llm_response(raw)
        assert pred.confidence == 1.0

    def test_confidence_below_zero_clamped_to_zero(self):
        """Case 6: confidence=-0.2 → clamped to 0.0."""
        raw = _make_raw(confidence=-0.2)
        pred = parse_llm_response(raw)
        assert pred.confidence == 0.0

    def test_confidence_at_boundary_one_unchanged(self):
        raw = _make_raw(confidence=1.0)
        pred = parse_llm_response(raw)
        assert pred.confidence == 1.0

    def test_confidence_at_boundary_zero_unchanged(self):
        raw = _make_raw(confidence=0.0)
        pred = parse_llm_response(raw)
        assert pred.confidence == 0.0


class TestLabelNormalization:
    """Case 7: label="PHISHING" (uppercase) → normalized to "phishing"."""

    def test_uppercase_phishing_normalized(self):
        raw = _make_raw(label="PHISHING")
        pred = parse_llm_response(raw)
        assert pred.label == "phishing"

    def test_uppercase_safe_normalized(self):
        raw = _make_raw(label="SAFE")
        pred = parse_llm_response(raw)
        assert pred.label == "safe"

    def test_mixed_case_suspect_normalized(self):
        raw = _make_raw(label="Suspect")
        pred = parse_llm_response(raw)
        assert pred.label == "suspect"


class TestEmptyInput:
    """Case 8: Empty string input → raises ValueError."""

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_llm_response("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            parse_llm_response("   \n\t  ")


class TestInvalidJson:
    """Case 9: Completely invalid JSON → raises ValueError."""

    def test_plain_text_raises(self):
        with pytest.raises(ValueError):
            parse_llm_response("This is not JSON at all")

    def test_truncated_json_raises(self):
        with pytest.raises(ValueError):
            parse_llm_response('{"label": "phishing", "confidence":')

    def test_array_instead_of_object_raises(self):
        with pytest.raises(ValueError):
            parse_llm_response('["phishing", 0.9]')


# ===========================================================================
# llm/prompts.py
# ===========================================================================

class TestZeroShotPrompt:
    """Case 10: zero_shot_prompt returns a (str, str) tuple."""

    def test_returns_two_element_tuple(self):
        result = zero_shot_prompt("test message")
        assert isinstance(result, tuple) and len(result) == 2

    def test_both_elements_are_strings(self):
        system, user = zero_shot_prompt("test message")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_is_non_empty(self):
        system, _ = zero_shot_prompt("test message")
        assert len(system) > 0

    def test_user_prompt_contains_message(self):
        _, user = zero_shot_prompt("my secret test phrase")
        assert "my secret test phrase" in user


class TestFewShotPrompt:
    """Case 11: few_shot_prompt returns tuple; user prompt contains "Example"."""

    def test_returns_two_element_tuple(self):
        result = few_shot_prompt("test message")
        assert isinstance(result, tuple) and len(result) == 2

    def test_both_elements_are_strings(self):
        system, user = few_shot_prompt("test message")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_user_prompt_contains_example_word(self):
        """The few-shot user prompt uses 'Example input:' to label examples."""
        _, user = few_shot_prompt("test message")
        assert "Example" in user, (
            f"Expected 'Example' in few_shot user prompt, got:\n{user[:300]}"
        )

    def test_user_prompt_contains_at_least_one_example(self):
        _, user = few_shot_prompt("probe")
        # FEW_SHOT_EXAMPLES has 3 examples — at least one 'Example input:' marker
        assert user.count("Example input:") >= 1

    def test_user_prompt_contains_message(self):
        _, user = few_shot_prompt("my probe message")
        assert "my probe message" in user


class TestChainOfThoughtPrompt:
    """Case 12: chain_of_thought_prompt user prompt contains "Step 1"."""

    def test_returns_two_element_tuple(self):
        result = chain_of_thought_prompt("test message")
        assert isinstance(result, tuple) and len(result) == 2

    def test_both_elements_are_strings(self):
        system, user = chain_of_thought_prompt("test message")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_user_prompt_contains_step_1(self):
        """The CoT prompt explicitly includes 'Step 1:' in its addendum."""
        _, user = chain_of_thought_prompt("test message")
        assert "Step 1" in user or "step 1" in user.lower(), (
            f"Expected 'Step 1' or 'step 1' in CoT prompt, got:\n{user[:400]}"
        )

    def test_user_prompt_contains_message(self):
        _, user = chain_of_thought_prompt("my cot test message")
        assert "my cot test message" in user


class TestGetStrategy:
    """Cases 13–14: get_strategy() returns callable or raises ValueError."""

    def test_get_zero_shot_returns_callable(self):
        """Case 13: get_strategy("zero_shot") → returns callable."""
        fn = get_strategy("zero_shot")
        assert callable(fn)

    def test_zero_shot_callable_returns_tuple(self):
        fn = get_strategy("zero_shot")
        result = fn("hello")
        assert isinstance(result, tuple) and len(result) == 2

    def test_get_few_shot_returns_callable(self):
        fn = get_strategy("few_shot")
        assert callable(fn)

    def test_get_cot_returns_callable(self):
        fn = get_strategy("cot")
        assert callable(fn)

    def test_get_chain_of_thought_alias_returns_callable(self):
        fn = get_strategy("chain_of_thought")
        assert callable(fn)

    def test_unknown_strategy_raises_value_error(self):
        """Case 14: get_strategy("unknown_xyz") → raises ValueError."""
        with pytest.raises(ValueError, match="unknown_xyz"):
            get_strategy("unknown_xyz")

    def test_gibberish_strategy_raises_value_error(self):
        with pytest.raises(ValueError):
            get_strategy("gpt_turbo_42")

    def test_case_insensitive_and_hyphen_normalized(self):
        """get_strategy normalises case and hyphens."""
        fn_lower = get_strategy("zero_shot")
        fn_upper = get_strategy("ZERO-SHOT")
        assert fn_lower is fn_upper


# ===========================================================================
# llm/client.py — predict() fallback behavior
# ===========================================================================

class TestPredictFallback:
    """Case 15: When the Gemini API raises on every attempt, predict()
    returns the safe fallback Prediction (label=suspect, confidence=0.0)
    and does NOT re-raise the exception.
    """

    def _run_predict_with_mocked_failure(self, exc: Exception) -> Prediction:
        """Patch _call_gemini_once to always raise exc, then call predict()."""
        with patch("llm.client._call_gemini_once", side_effect=exc):
            from llm.client import predict
            return predict("some phishing email text", strategy="zero_shot")

    def test_fallback_does_not_raise(self):
        result = self._run_predict_with_mocked_failure(RuntimeError("API down"))
        assert isinstance(result, Prediction)

    def test_fallback_label_is_suspect(self):
        """The fallback is 'suspect', not 'safe' — erring on the cautious side."""
        result = self._run_predict_with_mocked_failure(ConnectionError("timeout"))
        assert result.label == "suspect"

    def test_fallback_confidence_is_zero(self):
        result = self._run_predict_with_mocked_failure(ValueError("bad JSON"))
        assert result.confidence == 0.0

    def test_fallback_has_llm_call_failed_flag(self):
        result = self._run_predict_with_mocked_failure(OSError("network error"))
        assert "llm_call_failed" in result.red_flags

    def test_fallback_reasoning_mentions_failure(self):
        result = self._run_predict_with_mocked_failure(RuntimeError("boom"))
        assert "failed" in result.reasoning.lower()

    def test_fallback_strategy_is_set(self):
        result = self._run_predict_with_mocked_failure(RuntimeError("boom"))
        assert result.strategy == "zero_shot"

    def test_fallback_latency_ms_is_set(self):
        result = self._run_predict_with_mocked_failure(RuntimeError("boom"))
        assert result.latency_ms is not None and result.latency_ms >= 0

    def test_fallback_on_http_500_style_error(self):
        result = self._run_predict_with_mocked_failure(Exception("500 Internal Server Error"))
        assert result.label == "suspect"
        assert result.confidence == 0.0

    def test_no_real_api_call_made(self):
        """Verify the mock was actually used (no real network traffic)."""
        mock_fn = MagicMock(side_effect=RuntimeError("forced"))
        with patch("llm.client._call_gemini_once", mock_fn):
            from llm.client import predict
            predict("test", strategy="zero_shot")
        # Should have been called RETRY_MAX_ATTEMPTS times (3 by default)
        assert mock_fn.call_count >= 1


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import subprocess
    subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(Path(__file__).parent.parent),
    )
