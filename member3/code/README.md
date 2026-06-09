# Phishing Detection LLM Evaluation Module
**Role: Member 3 - ML Researcher**

This repository contains the evaluation framework designed to assess the performance of Member 2's LLM pipeline across various prompting strategies (Zero-Shot, Few-Shot, Chain-of-Thought). It calculates cybersecurity-specific metrics (including the F2-Score), exports isolated misclassifications for auditing, and generates visual performance plots.

## Repository Layout
The evaluation engine expects the following directory structure for inputs and will dynamically generate the `eval/` outputs upon execution:

```text
Final_LLM/
├── data/samples/kaggle_dataset_v2.json     # Ground truth mappings
├── results/                                # Text logs from Member 2
└── member3/code/
    ├── run_experiments.py                  # Main orchestrator
    ├── config.py                           # Central path/pricing controls
    └── eval/                               # Output directory (Auto-generated)