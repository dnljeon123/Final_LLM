import os
import json
import re
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

class PhishingMetricsEvaluator:
    def __init__(self):
        self.pricing = config.PRICING

    def load_ground_truth(self, dataset_path: str) -> list:
        logging.info(f"Ingesting ground truth dataset from: {dataset_path}")
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except UnicodeDecodeError:
            with open(dataset_path, "r", encoding="utf-16") as f:
                raw_data = json.load(f)
        
        return [{
            "id": item.get("name", f"record_{idx}"),
            "label": item["label"],
            "text": item.get("text", "")
        } for idx, item in enumerate(raw_data) if "label" in item]

    def parse_prediction_log(self, txt_path: str) -> list:
        logging.info(f"Parsing prediction log from: {txt_path}")
        predictions = []
        
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(txt_path, "r", encoding="utf-16") as f:
                lines = f.readlines()
                
        for line in lines:
            if "] verdict=" not in line:
                continue
            
            verdict_match = re.search(r"verdict=(\w+)", line)
            latency_match = re.search(r"latency=(\d+)ms", line)
            
            if verdict_match:
                verdict_str = verdict_match.group(1).lower()
                pred_label = 1 if verdict_str == "phishing" else 0
                latency = int(latency_match.group(1)) if latency_match else 0
                
                predictions.append({
                    "predicted_label": pred_label,
                    "latency_ms": latency,
                    "status": "success"
                })
            else:
                predictions.append({
                    "predicted_label": 0,
                    "latency_ms": 0,
                    "status": "failed"
                })
                
        return predictions

    def evaluate_strategy(self, predictions: list, ground_truths: list, strategy: str) -> dict:
        eval_length = min(len(predictions), len(ground_truths))
        if eval_length == 0:
            logging.error("No overlap between predictions and ground truth.")
            return {}

        results = []
        misclassified = []
        
        for i in range(eval_length):
            pred = predictions[i]
            truth = ground_truths[i]
            
            prompt_tokens = len(truth["text"]) // 4
            if strategy == "zero_shot":
                comp_tokens = 50
            elif strategy == "few_shot":
                comp_tokens = 150
            else:
                comp_tokens = 300

            res = {
                "id": truth["id"],
                "text": truth["text"],
                "true_label": truth["label"],
                "predicted_label": pred["predicted_label"],
                "latency_ms": pred["latency_ms"],
                "status": pred["status"],
                "prompt_tokens": prompt_tokens,
                "completion_tokens": comp_tokens
            }
            results.append(res)
            
            if res["status"] == "success" and res["true_label"] != res["predicted_label"]:
                error_type = "False Positive (Flagged Safe Email)" if res["predicted_label"] == 1 else "False Negative (Missed Threat)"
                misclassified.append({
                    "id": res["id"],
                    "error_type": error_type,
                    "true_label": res["true_label"],
                    "predicted_label": res["predicted_label"],
                    "text_preview": res["text"][:250] + "..." if len(res["text"]) > 250 else res["text"]
                })

        os.makedirs(config.MISCLASSIFICATIONS_DIR, exist_ok=True)
        with open(os.path.join(config.MISCLASSIFICATIONS_DIR, f"{strategy}_errors.json"), "w", encoding="utf-8") as f:
            json.dump(misclassified, f, indent=4)

        return self._calculate_statistics(results)

    def _calculate_statistics(self, results: list) -> dict:
        df = pd.DataFrame(results)
        
        valid_df = df[df["status"] == "success"]
        failure_rate = (len(df) - len(valid_df)) / len(df) if len(df) > 0 else 0

        if valid_df.empty:
            return {"failure_rate": failure_rate}

        y_true = valid_df["true_label"].tolist()
        y_pred = valid_df["predicted_label"].tolist()

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

        beta = 2.0
        if (beta**2 * prec + rec) == 0:
            f2 = 0.0
        else:
            f2 = (1 + beta**2) * (prec * rec) / ((beta**2 * prec) + rec)

        latencies = valid_df["latency_ms"].tolist()
        p50 = np.percentile(latencies, 50) if latencies else 0
        p95 = np.percentile(latencies, 95) if latencies else 0
        avg_latency = np.mean(latencies) if latencies else 0

        total_input_tokens = valid_df["prompt_tokens"].sum()
        total_output_tokens = valid_df["completion_tokens"].sum()
        projected_cost = (
            (total_input_tokens / 1000) * self.pricing["input_per_1k"] +
            (total_output_tokens / 1000) * self.pricing["output_per_1k"]
        )

        length_buckets = {"Short (<300)": [], "Medium (300-1K)": [], "Long (>1K)": []}
        for _, row in valid_df.iterrows():
            char_len = len(row["text"])
            is_correct = 1 if row["true_label"] == row["predicted_label"] else 0
            
            if char_len < 300:
                length_buckets["Short (<300)"].append(is_correct)
            elif char_len <= 1000:
                length_buckets["Medium (300-1K)"].append(is_correct)
            else:
                length_buckets["Long (>1K)"].append(is_correct)

        bucket_accuracy = {k: float(np.mean(v)) if v else 0.0 for k, v in length_buckets.items()}

        return {
            "evaluated_records": len(df),
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "f2_score": round(float(f2), 4),
            "confusion_matrix": cm.tolist(),
            "p50_latency_ms": round(float(p50), 2),
            "p95_latency_ms": round(float(p95), 2),
            "average_latency_ms": round(float(avg_latency), 2),
            "projected_cost_usd": round(float(projected_cost), 5),
            "failure_rate": round(float(failure_rate), 4),
            "bucket_accuracy": bucket_accuracy,
            "raw_latencies": latencies 
        }

    def print_performance_report(self, metrics: dict, strategy: str):
        if not metrics or "accuracy" not in metrics:
            print(f"\n=> EXPERIMENT RESULTS: {strategy.upper()} STRATEGY")
            print("   [!] Insufficient valid data to generate report.")
            return

        print(f"\n=> EXPERIMENT RESULTS: {strategy.upper()} STRATEGY (N={metrics['evaluated_records']})")
        print(f"   Accuracy            : {metrics['accuracy']:.4f}")
        print(f"   Precision           : {metrics['precision']:.4f}")
        print(f"   Recall (Phish Catch): {metrics['recall']:.4f}")
        print(f"   Security F1-Score   : {metrics['f1_score']:.4f}")
        print(f"   Security F2-Score   : {metrics['f2_score']:.4f}")
        print(f"   API Failure Rate    : {metrics['failure_rate']:.2%}")
        print(f"   Avg Latency         : {metrics['average_latency_ms']} ms")
        print(f"   Projected Cost      : ${metrics['projected_cost_usd']:.5f}")
        
        cm = metrics["confusion_matrix"]
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        
        print("\n" + "="*75)
        print("                         CONFUSION MATRIX DETAILS                        ")
        print("="*75)
        print("                        Predicted SAFE        Predicted PHISHING         ")
        print(f"Actual SAFE             [  {tn:<4}  ] (TN)      [  {fp:<4}  ] (FP)           ")
        print(f"Actual PHISHING         [  {fn:<4}  ] (FN)      [  {tp:<4}  ] (TP)           ")
        print("="*75 + "\n")

    def generate_visualizations(self, results_dict: dict, output_dir: str):
        logging.info("Generating comparative performance graphs.")
        os.makedirs(output_dir, exist_ok=True)
        
        strategies = list(results_dict.keys())
        if not strategies:
            return

        metrics_df = pd.DataFrame(results_dict).T
        core_metrics = ["accuracy", "precision", "recall", "f2_score"]
        if all(m in metrics_df.columns for m in core_metrics):
            ax = metrics_df[core_metrics].plot(kind="bar", figsize=(10, 6), colormap="viridis")
            plt.title("Cross-Validation: Security Metrics by Prompting Strategy")
            plt.ylabel("Score (0.0 to 1.0)")
            plt.ylim(0, 1.1)
            plt.xticks(rotation=0)
            plt.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "metric_comparison.png"))
            plt.close()

        buckets = ["Short (<300)", "Medium (300-1K)", "Long (>1K)"]
        bucket_data = {s: [results_dict[s]["bucket_accuracy"].get(b, 0) for b in buckets] for s in strategies}
        
        plt.figure(figsize=(10, 6))
        for strategy, accuracies in bucket_data.items():
            plt.plot(buckets, accuracies, marker="o", linestyle="-", label=strategy.replace("_", " ").title(), linewidth=2)
        
        plt.title("Accuracy Decay Across Email Character Lengths")
        plt.xlabel("Input Length Segment")
        plt.ylabel("Accuracy")
        plt.ylim(0, 1.1)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(title="Strategy")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "length_accuracy_decay.png"))
        plt.close()

        plt.figure(figsize=(8, 6))
        for strategy in strategies:
            cost = results_dict[strategy].get("projected_cost_usd", 0)
            f2 = results_dict[strategy].get("f2_score", 0)
            plt.scatter(cost, f2, s=150, label=strategy.replace("_", " ").title())
            plt.annotate(strategy.replace("_", " ").title(), (cost, f2), xytext=(5, 5), textcoords='offset points')
            
        plt.title("Cost vs. F2-Score Efficiency Trade-off")
        plt.xlabel("Projected Cost per Batch (USD)")
        plt.ylabel("Security F2-Score (Recall Weighted)")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "cost_efficiency_tradeoff.png"))
        plt.close()

        latency_data = [results_dict[s].get("raw_latencies", []) for s in strategies]
        plt.figure(figsize=(8, 6))
        plt.boxplot(latency_data, tick_labels=[s.replace("_", " ").title() for s in strategies], patch_artist=True)
        plt.title("Latency Distribution by Strategy (Median & Variance)")
        plt.ylabel("Latency (ms)")
        plt.grid(True, axis="y", linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "latency_boxplot.png"))
        plt.close()