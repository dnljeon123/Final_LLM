import os
import json
import logging
import config
from eval.evaluator import PhishingMetricsEvaluator

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def main():
    print("\n" + "="*75)
    print("           CYBER SECURITY EXPERIMENT EXECUTION ENGINE (WEEK 16)          ")
    print("=========================================================================\n")

    evaluator = PhishingMetricsEvaluator()
    
    try:
        ground_truths = evaluator.load_ground_truth(config.DATASET_PATH)
    except FileNotFoundError:
        logging.error(f"Ground truth dataset not found at {config.DATASET_PATH}. Please verify the path in config.py.")
        return

    final_results = {}

    for strategy, filepath in config.STRATEGY_FILES.items():
        try:
            predictions = evaluator.parse_prediction_log(filepath)
            metrics = evaluator.evaluate_strategy(predictions, ground_truths, strategy)
            
            evaluator.print_performance_report(metrics, strategy)
            final_results[strategy] = metrics
        except FileNotFoundError:
            logging.error(f"Prediction log missing at {filepath}. Skipping {strategy}.")

    evaluator.generate_visualizations(final_results, config.PLOTS_DIR)

    # Clean raw array lists from JSON before exporting
    for strat in final_results:
        final_results[strat].pop("raw_latencies", None)
        final_results[strat].pop("bucket_accuracy", None)

    os.makedirs(os.path.dirname(config.OUTPUT_REPORT_PATH), exist_ok=True)
    with open(config.OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
        
    logging.info(f"Evaluation metrics compiled and exported to {config.OUTPUT_REPORT_PATH}")
    logging.info(f"Misclassifications exported to '{config.MISCLASSIFICATIONS_DIR}/' directory.")
    logging.info(f"Graphs successfully rendered in '{config.PLOTS_DIR}/' directory.")

if __name__ == "__main__":
    main()