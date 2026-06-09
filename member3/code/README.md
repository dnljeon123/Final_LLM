# Phishing Detection LLM Evaluation Module
**Role: Member 3 - ML Researcher**

This repository contains the evaluation framework designed to assess the performance of Member 2's LLM pipeline across various prompting strategies (Zero-Shot, Few-Shot, Chain-of-Thought). It calculates cybersecurity-specific metrics (including the F2-Score), exports isolated misclassifications for auditing, and generates visual performance plots.

## Repository Layout
The evaluation engine expects the following directory structure for inputs and will dynamically generate the `eval/` outputs upon execution:

```text
Final_LLM/
├── Final_2/                                 <-- (Member 1's Dataset Source)
│   └── poc/
│       └── data/
│           └── samples/
│               └── kaggle_dataset_v2.json
├── member2/                                 <-- (Member 2's Result Logs)
│   └── result/
│       ├── zeroshot_gemini.txt
│       ├── fewshot_gemini.txt
│       └── cot_gemini.txt
└── member3/                                 <-- (this module workspace)
    ├── .gitignore
    ├── README.md
    └── code/
        ├── requirements.txt				
        ├── config.py						
        ├── run_experiments.py				 <-- (Run this file)
		├
        └── eval/                            <-- (output directory)
            ├── results_summary.json         <-- (Final metrics)
            ├── misclassifications/          <-- (Threat-leak error reports)
            └── plots/                       <-- (Visual analysis)