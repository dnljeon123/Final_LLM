# Module 2: LLM Prompt Engineering & Phishing Classification

**Owner: Member 2 — LLM Engineer**

This directory contains the LLM integration layer for the LLM Phishing Detection
project. It implements and evaluates three prompt engineering strategies
(Zero-shot, Few-shot, Chain-of-Thought) against a 1,000-sample labeled dataset
using the Gemini 2.5 Flash Lite API.

The module handles API communication, prompt construction, response parsing,
and outputs per-sample prediction logs consumed by Member 3's evaluation engine.

---

## Execution Context

This module expects to be run from the root directory of the `Final_LLM`
repository to properly access shared data and result folders.

---

## Setup

Ensure you are in the `Final_LLM/` root directory, then install dependencies:

```bash
pip install -r member2/requirements.txt
```

Set your Gemini API key:

```bash
# Linux/Mac
export GEMINI_API_KEY="your_key_here"

# Windows PowerShell
$env:GEMINI_API_KEY = "your_key_here"
```

> Free-tier API key available at: https://aistudio.google.com/apikey

---

## Run Evaluation

```bash
# Zero-shot
python -m member2.eval.harness --strategy zero_shot --test-set member2/data/samples/kaggle_dataset_v2.json

# Few-shot
python -m member2.eval.harness --strategy few_shot --test-set member2/data/samples/kaggle_dataset_v2.json

# Chain-of-Thought
python -m member2.eval.harness --strategy cot --test-set member2/data/samples/kaggle_dataset_v2.json
```

Each run takes ~17 minutes (1 req/sec × 1,000 samples). Results are saved to `member2/results/`.

---

## Output Format

Each result file (`results/*_gemini.txt`) contains one JSON prediction per line
followed by a metrics block at the end:

```
{"id": 42, "label": 1, "pred": 1, "conf": 0.95, "strategy": "zero_shot"}
{"id": 43, "label": 0, "pred": 0, "conf": 0.88, "strategy": "zero_shot"}
...

=== Strategy: zero_shot | Total samples: 1000 ===
Accuracy     : 0.6740
Precision    : 0.6408
Recall       : 0.7920
F1           : 0.7084
Failure rate : 0.0000
```

> **For Member 3:** Prediction logs are located at:
> `Final_LLM/member2/results/zeroshot_gemini.txt`
> `Final_LLM/member2/results/fewshot_gemini.txt`
> `Final_LLM/member2/results/cot_gemini.txt`

---

## Results Summary (n=1,000)

| Strategy | Accuracy | Precision | Recall | F1 | Failure Rate |
|----------|----------|-----------|--------|----|--------------|
| **Zero-shot** | **0.674** | **0.641** | **0.792** | **0.708** | 0.0% |
| Few-shot | 0.661 | 0.640 | 0.736 | 0.685 | 0.1% |
| CoT | 0.623 | 0.621 | 0.632 | 0.626 | 4.4% |

**Key finding:** Zero-shot outperforms both Few-shot and CoT on all metrics.
CoT's 4.4% failure rate (JSON parse errors on verbose output) drags accuracy down.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | Gemini API key |
| `LLM_MODEL` | No | `gemini-2.5-flash-lite` | Model name |
| `LLM_MAX_TOKENS` | No | `2048` | Max output tokens |
| `LLM_TEMPERATURE` | No | `0.0` | Sampling temperature |

---

## Known Issues

- CoT strategy has a 4.4% failure rate due to JSON parse errors on verbose output — fallback label is `suspect` with `conf=0.00`
- Free-tier Gemini is rate-limited to 9 RPM → set `GEMINI_RPM=9` in `config.py`
- Dataset labels are integers (`0`/`1`), not strings

---

## Contact

Member 2 — Nguyen Duc Thien | GitHub: [@NgThien182002](https://github.com/NgThien182002)
