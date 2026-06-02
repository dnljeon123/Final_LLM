import os
import json
import logging
import random
from eval.harness import PhishingEvaluationHarness
from eval.analyze import PhishingEvaluationAnalyzer

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def main():
    print("\n" + "="*75)
    print("           CYBER SECURITY EXPERIMENT EXECUTION ENGINE (WEEK 15)          ")
    print("=========================================================================")

    harness = PhishingEvaluationHarness()
    analyzer = PhishingEvaluationAnalyzer()

    dataset_path = "data/samples/kaggle_dataset_v2.json"
    records = harness.load_evaluation_data(dataset_path)

    test_size = int(len(records) * 0.2)
    random.seed(42)
    test_records = random.sample(records, test_size)
    
    logging.info(f"Ingested {len(test_records)} evaluation records from the central dataset.")

    results_by_strategy = {}
    strategies = ["zero_shot", "few_shot", "chain_of_thought"]

    for strategy in strategies:
        print("\n" + "-"*75)
        raw_results = harness.execute_batch_evaluation(test_records, strategy)
        audited_results = analyzer.run_dual_llm_as_a_judge(raw_results)
        metrics = analyzer.analyze_metrics(audited_results)
        results_by_strategy[strategy] = metrics

        print(f"\n=> EXPERIMENT RESULTS: {strategy.upper()} STRATEGY")
        print(f"   Accuracy            : {metrics['accuracy']:.4f}")
        print(f"   Recall (Phish Catch): {metrics['recall']:.4f}")
        print(f"   Security F2-Score   : {metrics['f2_score']:.4f}")
        print(f"   Avg Latency         : {metrics['average_latency_sec']:.3f} seconds")
        print(f"   Total Token Cost    : ${metrics['total_cost_usd']:.5f}")
        
        analyzer.print_text_confusion_matrix(metrics["confusion_matrix"])

    output_report_path = "eval/results_summary.json"
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(results_by_strategy, f, indent=4, ensure_ascii=False)
        
    logging.info(f"Evaluation summary compiled successfully and exported to {output_report_path}")
    print("\n" + "="*75)
    print("                EXPERIMENTS COMPLETED - PIPELINE INTEGRATION OK          ")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()