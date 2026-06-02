import os
import json
import time
import random
import logging
from typing import List, Dict, Any, Callable

logging.basicConfig(
    level=logging.INFO, 
    format="[%(asctime)s] %(levelname)s: %(message)s"
)

class PhishingEvaluationHarness:
    def __init__(self, predictor_client: Callable[[Dict[str, Any], str], Dict[str, Any]] = None):
        self.predictor_client = predictor_client if predictor_client else self._mock_gemini_client
        self.raw_results_log = []

    def _mock_gemini_client(self, record: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        simulated_latency = random.uniform(0.6, 1.2) if strategy != "chain_of_thought" else random.uniform(1.4, 2.5)
        time.sleep(simulated_latency)

        auth = record.get("auth_status", {})
        clean_text = record.get("clean_text", "").lower()
        sender = record.get("sender", "").lower()
        urls = record.get("urls", [])

        red_flags = []
        is_phish = False
        confidence = 0.50

        if auth.get("dmarc") == "fail" or auth.get("spf") == "fail":
            red_flags.append("dmarc_fail: SPF/DMARC alignment failed")
            is_phish = True
            confidence += 0.35

        if "paypa1" in sender or "secure-" in sender or "support-update" in sender:
            red_flags.append(f"lookalike_domain: Mismatched domain signature in sender '{sender}'")
            is_phish = True
            confidence += 0.25

        urgency_markers = ["limit", "suspend", "action required", "24 hours", "unauthorized", "immediately"]
        if any(marker in clean_text for marker in urgency_markers):
            red_flags.append("urgency_language: High-pressure urgency framing detected")
            is_phish = True
            confidence += 0.15

        if len(urls) > 0:
            red_flags.append("suspicious_url: External link targets unverified domain")

        if is_phish:
            label = "phishing"
            confidence = min(confidence, 0.99)
            reasoning = f"Threat confirmed. Found critical markers: {', '.join(red_flags[:2])}."
        else:
            label = "safe"
            confidence = round(random.uniform(0.85, 0.98), 2)
            reasoning = "The message passes baseline verification and contains no obvious social engineering patterns."

        prompt_tokens = len(clean_text) // 4 + (150 if strategy == "zero_shot" else 450)
        completion_tokens = len(reasoning) // 4 + (200 if strategy == "chain_of_thought" else 50)

        return {
            "label": label,
            "confidence": round(confidence, 2),
            "red_flags": red_flags,
            "reasoning": reasoning,
            "usage_metadata": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
        }

    def load_evaluation_data(self, file_path: str) -> List[Dict[str, Any]]:
        if os.path.exists(file_path):
            logging.info(f"Loading preprocessed dataset from: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            records = []
            for idx, item in enumerate(raw_data):
                records.append({
                    "id": item.get("id", f"msg_{idx:04d}"),
                    "clean_text": item.get("text", item.get("clean_text", "")),
                    "sender": item.get("sender", "unknown@domain.com"),
                    "urls": item.get("urls", []),
                    "auth_status": item.get("auth_status", {"spf": "none", "dkim": "none", "dmarc": "none"}),
                    "label": item.get("label", 0)
                })
            return records
        else:
            logging.warning(f"File {file_path} not found. Initializing 20 mock verification records...")
            return self._generate_fallback_samples()

    def _generate_fallback_samples(self) -> List[Dict[str, Any]]:
        samples = []
        for i in range(10):
            samples.append({
                "id": f"phish_{i}",
                "clean_text": "Security Alert: Your payment details require immediate verification. Log in within 24 hours.",
                "sender": "service@paypa1-support.com",
                "urls":