import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Callable
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

class PhishingEvaluationAnalyzer:
    def __init__(self, judge_a_client: Callable[[str], str] = None, judge_b_client: Callable[[str], str] = None):
        self.judge_a_client = judge_a_client
        self.judge_b_client = judge_b_client
        self.pricing = {
            "input_per_1k": 0.00015,
            "output_per_1k": 0.00060
        }

    def analyze_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        df = pd.DataFrame(results)
        valid_df = df[df["status"] == "success"]
        
        if valid_df.empty:
            logging.error("No valid evaluation data available.")
            return {}

        y_true = valid_df["true_label"].tolist()
        y_pred = valid_df["predicted_label"].tolist()

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)

        beta = 2.0
        if (beta**2 * prec + rec) == 0:
            f2 = 0.0
        else:
            f2 = (1 + beta**2) * (prec * rec) / ((beta**2 * prec) + rec)

        latencies = valid_df["latency"].values
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        avg_latency = np.mean(latencies)

        total_input_tokens = valid_df["prompt_tokens"].sum()
        total_output_tokens = valid_df["completion_tokens"].sum()
        total_cost = (
            (total_input_tokens / 1000) * self.pricing["input_per_1k"] +
            (total_output_tokens / 1000) * self.pricing["output_per_1k"]
        )

        return {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "f2_score": round(float(f2), 4),
            "confusion_matrix": cm.tolist(),
            "p50_latency_sec": round(float(p50), 3),
            "p95_latency_sec": round(float(p95), 3),
            "average_latency_sec": round(float(avg_latency), 3),
            "total_cost_usd": round(float(total_cost), 5)
        }

    def print_text_confusion_matrix(self, cm: List[List[int]]) -> None:
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        print("\n" + "="*75)
        print("                         CONFUSION MATRIX DETAILS                        ")
        print("="*75)
        print("                        Predicted SAFE        Predicted PHISHING         ")
        print(f"Actual SAFE             [  {tn:<4}  ] (TN)      [  {fp:<4}  ] (FP)           ")
        print(f"Actual PHISHING         [  {fn:<4}  ] (FN)      [  {tp:<4}  ] (TP)           ")
        print("="*75)
        print(f"True Positives (Correctly Stopped Phishing)  : {tp}")
        print(f"False Negatives (Missed Phishing - Risk)     : {fn}  <--- Threat Leak")
        print(f"False Positives (Incorrectly Flagged Benign) : {fp}")
        print("="*75 + "\n")

    def run_dual_llm_as_a_judge(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.judge_a_client or not self.judge_b_client:
            logging.warning("Dual-Judge APIs not fully linked. Generating baseline simulation scores.")
            return self._run_mock_judge(results)

        logging.info("Initiating Dual-Model automated reasoning evaluation.")
        audited_results = []

        for entry in results:
            if entry.get("status") != "success":
                entry["judge_a_score"] = 1
                entry["judge_b_score"] = 1
                audited_results.append(entry)
                continue

            reasoning_to_grade = entry["reasoning"]

            prompt_a = f"""
            System Role: You are a strict Technical Mail Security Auditor.
            Evaluate the following AI classification reasoning for technical accuracy regarding SPF, DKIM, DMARC, and domain mapping:
            
            AI Verdict: {entry['predicted_label']}
            AI Reasoning: {reasoning_to_grade}
            
            Assign a single integer score (1, 3, or 5):
            Score 5: Technically flawless explanation of domain markers or verification records.
            Score 3: Correct decision but technically shallow or generic.
            Score 1: Hallucinated technical facts or inaccurate authentication claims.
            
            Respond only with valid JSON: {{"score": <1, 3, or 5>, "feedback": "<one-sentence reasoning>"}}
            """

            prompt_b = f"""
            System Role: You are a Cognitive Threat Analyst specializing in social engineering.
            Evaluate the following AI reasoning on how well it identifies psychological traps, framing, or urgency markers:
            
            AI Verdict: {entry['predicted_label']}
            AI Reasoning: {reasoning_to_grade}
            
            Assign a single integer score (1, 3, or 5):
            Score 5: Excellent analysis of urgency cues, threat framing, or bait tactics.
            Score 3: Generic assessment of tone without detailed cognitive analysis.
            Score 1: Complete failure to explain how the social engineering attempt works.
            
            Respond only with valid JSON: {{"score": <1, 3, or 5>, "feedback": "<one-sentence reasoning>"}}
            """

            try:
                resp_a = self.judge_a_client(prompt_a)
                parsed_a = json.loads(resp_a.strip())
                entry["judge_a_score"] = parsed_a.get("score", 3)
                entry["judge_a_feedback"] = parsed_a.get("feedback", "")

                resp_b = self.judge_b_client(prompt_b)
                parsed_b = json.loads(resp_b.strip())
                entry["judge_b_score"] = parsed_b.get("score", 3)
                entry["judge_b_feedback"] = parsed_b.get("feedback", "")

            except Exception as e:
                logging.error(f"Audit processing error for {entry['id']}: {str(e)}")
                entry["judge_a_score"] = 3
                entry["judge_b_score"] = 3

            audited_results.append(entry)

        return audited_results

    def _run_mock_judge(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for entry in results:
            if entry["predicted_label"] == entry["true_label"]:
                entry["judge_a_score"] = random.choice([3, 5, 5])
                entry["judge_b_score"] = random.choice([3, 5, 5])
            else:
                entry["judge_a_score"] = random.choice([1, 1, 3])
                entry["judge_b_score"] = random.choice([1, 1, 3])
        return results