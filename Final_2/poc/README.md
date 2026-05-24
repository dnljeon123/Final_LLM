# Phishing Detector — LLM-Powered Cybersecurity PoC

A Proof of Concept system that uses Large Language Models to detect phishing emails and SMS, with three swappable prompt strategies (Zero-shot, Few-shot, Chain-of-Thought) and a Gradio web demo.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key (free at https://aistudio.google.com/apikey)
export GEMINI_API_KEY="your-key-here"

# 3. Launch the web demo
python app.py
```

The Gradio UI opens at http://localhost:7860.

## Project structure

```
poc/
├── README.md
├── requirements.txt
├── app.py                  # Gradio web demo entry point
├── config.py               # API keys, settings
├── pipeline.py             # End-to-end orchestrator
├── data/
│   ├── preprocessor.py     # .eml / CSV / text -> Record
│   ├── datasets.py         # Dataset loaders
│   └── samples/            # Demo input files
├── llm/
│   ├── client.py           # Gemini API wrapper with retry
│   ├── prompts.py          # Three prompt strategies
│   └── schema.py           # JSON output validation
├── eval/
│   ├── harness.py          # Run a strategy on a test set
│   ├── metrics.py          # Accuracy, Precision, Recall, F1
│   └── analyze.py          # Error analysis
└── tests/                  # Unit tests
```

## Running evaluation

```bash
# Evaluate Chain-of-Thought on the test set
python -m eval.harness --strategy cot --test-set data/samples/test.json

# Compare all three strategies
python -m eval.harness --compare-all --test-set data/samples/test.json
```

## Architecture

The system has four layers:

1. **Data ingestion** — accepts .eml, CSV, plain text
2. **Preprocessing** — HTML stripping, URL extraction, header parsing
3. **LLM core** — three prompt strategies routed through a Gemini client
4. **Output** — structured JSON with verdict, confidence, red flags, reasoning

## Team

| Member | Role | Module |
|---|---|---|
| Member 1 | Data Engineer | `data/` |
| Member 2 | LLM Engineer | `llm/` |
| Member 3 | ML Researcher | `eval/` |
| Member 4 | Integrator | `app.py`, `pipeline.py` |

## License & Datasets

This is an academic project. Datasets used:
- Nazario Phishing Corpus (academic use)
- Enron Email Dataset (public)
- UCI SMS Spam Collection (public)

## Notes

- All experiments use temperature=0 for determinism.
- Default LLM is Gemini 1.5 Flash; the client is provider-agnostic.
- The Gradio demo's public share link (gradio.live) expires in 72 hours.
