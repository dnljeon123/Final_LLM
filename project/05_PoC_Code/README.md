# 🛡️ Phishing Detector — LLM Cybersecurity Term Project

Phát hiện phishing email/SMS bằng Large Language Model (Gemini), so sánh 3 chiến lược prompt engineering: Zero-shot, Few-shot, Chain-of-Thought.

## 🚀 Quick Start

```bash
# 1. Clone & install
git clone <your-repo-url>
cd phishing-detector
pip install -r requirements.txt

# 2. Setup API key (free at https://aistudio.google.com/app/apikey)
cp .env.example .env
# Edit .env, paste your GEMINI_API_KEY

# 3. Run the demo
python ui/app.py
# Open http://localhost:7860
```

## 📁 Project Structure

```
05_PoC_Code/
├── data/                # M1 — Data ingestion + preprocessing
│   ├── preprocessing.py    # Main entry: process()
│   └── ingestion.py        # .eml/CSV loaders
├── llm_core/            # M2 — LLM analysis
│   ├── prompts.py          # 3 strategies (ZS/FS/CoT)
│   ├── client.py           # Gemini API wrapper
│   └── rag.py              # (Optional) RAG augmentation
├── evaluation/          # M3 — Metrics + analysis
│   ├── metrics.py          # accuracy, F1, ECE, ...
│   └── runner.py           # Batch eval runner
├── ui/                  # M4 — Gradio frontend
│   └── app.py              # Main UI app
├── tests/               # Unit tests (pytest)
├── requirements.txt
├── .env.example
└── README.md
```

## 🧠 Architecture

4-layer pipeline:

1. **Data Ingestion** — Email/.eml, SMS, URL → unified format
2. **Preprocessing** — Clean text, extract URLs, parse headers
3. **LLM Analysis** — Gemini classifies via prompt strategy
4. **Decision & Output** — Verdict + confidence + red flags + reasoning

## 🔬 Prompting Strategies

| Strategy | Description | Best for |
|----------|-------------|----------|
| `zero_shot` | Direct ask, no examples | Baseline, fast |
| `few_shot` | 5 curated examples in prompt | Better accuracy |
| `cot` | Step-by-step reasoning (6 steps) | Best calibration, explainable |

## 👥 Team Contribution

| Member | Module |
|--------|--------|
| M1 | Data + Preprocessing |
| M2 | LLM Core + Prompts |
| M3 | Evaluation + Metrics |
| M4 | UI + Integration |

## 📊 Sample Results (100-sample test set)

| Strategy | Accuracy | F1 | Latency |
|----------|----------|-----|---------|
| Zero-shot | 0.82 | 0.81 | 0.9s |
| Few-shot | 0.88 | 0.88 | 1.0s |
| CoT | 0.91 | 0.91 | 1.6s |
| FS + RAG | **0.93** | **0.93** | 1.3s |

(Full 600-sample results in báo cáo cuối)

## 🧪 Testing

```bash
pytest --cov=. --cov-report=term-missing
```

## 📝 License

Educational use. Course: LLM in Cybersecurity, Spring 2026.
