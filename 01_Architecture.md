# KIẾN TRÚC HỆ THỐNG — PHISHING DETECTION SYSTEM

## 1. Tổng quan

Hệ thống được thiết kế theo kiến trúc 4 tầng (4-layer architecture), modular, mỗi tầng có interface rõ ràng để 4 thành viên có thể phát triển song song.

```
┌─────────────────────────────────────────────────────────┐
│  TẦNG 1: DATA INGESTION                                 │
│  Email (.eml/IMAP) │ SMS/Chat │ URLs/Files              │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  TẦNG 2: PREPROCESSING & FEATURE EXTRACTION             │
│  Text cleaning │ URL extract │ Header parse │ Metadata  │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  TẦNG 3: LLM ANALYSIS CORE                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Prompt Eng. │→ │ LLM API call │← │ RAG (opt.)   │    │
│  │ ZS/FS/CoT   │  │ Gemini Flash │  │ FAISS + emb. │    │
│  └─────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  TẦNG 4: DECISION & OUTPUT                              │
│  Classification │ Confidence │ Explanation (red flags)  │
└─────────────────────────┬───────────────────────────────┘
                          ↓
                   ┌──────────────┐
                   │ Evaluation   │
                   │ Acc/F1/P/R   │
                   └──────────────┘
```

---

## 2. Chi tiết từng tầng

### Tầng 1 — Data Ingestion (Owner: M1)

**Trách nhiệm:** Nhận input dạng raw, đưa về unified format.

**Input formats:**
- File `.eml` (email chuẩn RFC 5322)
- File `.txt` (SMS, chat message)
- File `.csv` (batch processing)
- URL (single string)

**Output format (unified JSON):**
```json
{
  "id": "msg_001",
  "type": "email" | "sms" | "url",
  "raw_content": "...",
  "metadata": {
    "received_at": "2026-01-15T10:30:00Z",
    "source": "imap" | "file" | "manual"
  }
}
```

---

### Tầng 2 — Preprocessing (Owner: M1)

**Trách nhiệm:** Extract features, làm sạch noise.

**Modules:**

1. **Text cleaner**
   - Strip HTML tags (BeautifulSoup)
   - Decode quoted-printable, base64
   - Normalize whitespace, encoding (UTF-8)

2. **URL extractor**
   - Regex extract all URLs
   - Resolve shortened URLs (bit.ly, tinyurl)
   - Detect homoglyph attacks (g00gle.com)

3. **Header parser** (email only)
   - Extract: From, Reply-To, Return-Path, Received chain
   - Check SPF/DKIM/DMARC records (nếu có)
   - Detect mismatch From vs Reply-To

4. **Metadata extractor**
   - Timestamps
   - Language detection (langdetect)
   - Attachment list

**Output:**
```json
{
  "id": "msg_001",
  "cleaned_text": "...",
  "urls": [{"url": "...", "resolved": "...", "suspicious_score": 0.7}],
  "headers": {...},
  "language": "en"
}
```

---

### Tầng 3 — LLM Analysis Core (Owner: M2)

**Trách nhiệm:** Phân tích bằng LLM, đây là phần research chính.

#### 3.1 Prompt Engineering Module

Triển khai 3 strategies để so sánh:

**A. Zero-shot prompting**
```
You are a cybersecurity expert. Analyze this message and 
determine if it is a phishing attempt.
Output JSON: {"label": "phishing|safe|suspect", "confidence": 0-1, 
              "reasons": ["..."]}

Message: {text}
```

**B. Few-shot prompting**
```
You are a cybersecurity expert. Here are examples:

Example 1: "Your account will be suspended. Click here to verify..."
Output: {"label": "phishing", "confidence": 0.95, 
         "reasons": ["urgency tactic", "suspicious link"]}

Example 2: "Hi Mom, dinner tomorrow at 7?"
Output: {"label": "safe", "confidence": 0.99, "reasons": ["personal context"]}

[3-5 more examples...]

Now analyze: {text}
```

**C. Chain-of-Thought (CoT) prompting**
```
Analyze this message step-by-step:

Step 1: Identify the claimed sender and their stated purpose
Step 2: Look for urgency/fear tactics
Step 3: Analyze any URLs - are they legitimate?
Step 4: Check for grammatical errors typical of phishing
Step 5: Look for requests for sensitive info (passwords, OTP)
Step 6: Make a final decision based on steps 1-5

Output JSON: {"reasoning": "...step-by-step...", 
              "label": "...", "confidence": ..., "reasons": [...]}

Message: {text}
```

#### 3.2 LLM API Client

- Wrap `google-generativeai` SDK
- Retry logic với exponential backoff
- Rate limit handling (Gemini Flash free tier: ~15 req/min)
- Response validation (JSON schema enforcement)
- Log mọi request/response để debug

#### 3.3 RAG Module (Optional, advanced)

- Build vector DB từ corpus phishing đã biết
- Embed bằng `sentence-transformers/all-MiniLM-L6-v2`
- Top-k retrieval (k=3) similar phishing examples
- Inject vào prompt như few-shot examples động

---

### Tầng 4 — Decision & Output (Owner: M4)

**Trách nhiệm:** Tổng hợp output, present cho user.

**Decision Schema:**
```json
{
  "message_id": "msg_001",
  "verdict": "phishing",
  "confidence": 0.87,
  "risk_level": "high",
  "red_flags": [
    "Urgency tactic detected: 'account suspended in 24h'",
    "Suspicious URL: paypa1-secure.com (homoglyph attack)",
    "Mismatch between sender domain and reply-to"
  ],
  "recommendation": "Do not click any links. Report to IT.",
  "llm_strategy": "chain-of-thought",
  "processing_time_ms": 1240
}
```

**Risk levels:**
- `low` (confidence < 0.3 → safe)
- `medium` (0.3-0.7 → suspect, manual review)
- `high` (> 0.7 → phishing, block)

---

### Evaluation Branch (Owner: M3)

**Test set:**
- 200 phishing emails (Nazario Corpus)
- 200 legitimate emails (Enron Sent folder)
- 100 SMS phishing (SMS Spam UCI)
- 100 legitimate SMS

**Metrics:**
- **Accuracy:** Overall correctness
- **Precision:** Của những cái flag là phishing, bao nhiêu đúng?
- **Recall:** Trong tất cả phishing thực sự, bắt được bao nhiêu?
- **F1-score:** Harmonic mean của P và R
- **Confusion Matrix:** Hiển thị TP/FP/TN/FN
- **Per-strategy comparison:** ZS vs FS vs CoT
- **Latency:** ms/request
- **Cost:** tokens/request (nếu dùng paid tier)

**Error Analysis:**
- Sample 20 false positives + 20 false negatives
- Phân tích thủ công nguyên nhân
- Đề xuất cải thiện

---

## 3. Data Flow ví dụ

```
User uploads email.eml
    ↓ (M4 — Gradio UI)
{type: "email", raw_content: "..."}
    ↓ (M1 — Preprocessing)
{cleaned_text: "...", urls: [...], headers: {...}}
    ↓ (M2 — LLM Core với CoT prompt)
{reasoning: "...", label: "phishing", confidence: 0.87, reasons: [...]}
    ↓ (M4 — Decision layer)
{verdict: "phishing", risk: "high", red_flags: [...], recommendation: "..."}
    ↓ (M4 — UI rendering)
Người dùng thấy kết quả + giải thích
```

---

## 4. Interface Contract giữa các module

**Đây là phần quan trọng — chốt cứng để 4 người làm song song:**

```python
# data_ingestion.py (M1)
def load_message(file_path: str) -> dict: ...
def preprocess(raw_message: dict) -> dict: ...

# llm_core.py (M2)
def analyze(preprocessed: dict, strategy: str = "cot") -> dict: ...
# strategy ∈ {"zero_shot", "few_shot", "cot"}

# evaluation.py (M3)
def evaluate(predictions: list, ground_truth: list) -> dict: ...
def plot_confusion_matrix(...) -> Figure: ...

# ui.py (M4)
def launch_demo(analyze_fn: callable): ...
```

Mỗi người chỉ cần đảm bảo function của mình match contract — không cần biết bên trong người khác làm gì.

---

## 5. Folder structure code

```
05_PoC_Code/
├── data/
│   ├── __init__.py
│   ├── ingestion.py      # M1
│   ├── preprocessing.py  # M1
│   └── datasets/         # raw data
├── llm_core/
│   ├── __init__.py
│   ├── prompts.py        # M2 — 3 prompt templates
│   ├── client.py         # M2 — Gemini API wrapper
│   └── rag.py            # M2 — optional RAG
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py        # M3
│   └── runner.py         # M3
├── ui/
│   ├── __init__.py
│   └── app.py            # M4 — Gradio app
├── tests/
├── requirements.txt
└── README.md
```
