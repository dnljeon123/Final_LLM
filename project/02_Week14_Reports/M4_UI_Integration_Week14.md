# BÁO CÁO CÁ NHÂN — TUẦN 14
**Member 4 — UI & System Integration**

> *Họ tên:* [Điền tên]
> *MSSV:* [Điền MSSV]
> *Nhóm:* [Số nhóm]
> *Đề tài:* Phishing Detection using LLM
> *Vai trò:* Frontend Demo & System Integration

---

## 1. Giới thiệu

Project term này nhóm chúng tôi xây dựng hệ thống phát hiện phishing dùng LLM. Tôi đảm nhận **UI demo và tích hợp toàn hệ thống**. Vai trò này tuy không "research-heavy" như M2-M3 nhưng cực kỳ quan trọng: nó là **bộ mặt của project khi demo và đánh giá**, đồng thời là **chất keo** kết nối các module rời rạc của 3 thành viên khác thành một sản phẩm hoàn chỉnh.

## 2. Vai trò trong tổng thể hệ thống

Tôi phụ trách 2 mảng:

**(a) UI Demo (Frontend)**
- Cho phép user upload email/SMS, nhận kết quả phân loại + giải thích
- Hiển thị metrics dashboard
- Demo trực quan cho thầy/cô khi present

**(b) System Integration**
- Đảm bảo M1→M2→M3 chạy seamless end-to-end
- Setup CI/CD, environment, deployment
- Quản lý GitHub repo, code review

## 3. Research

### 3.1 Lựa chọn UI Framework

Tôi đã so sánh các framework:

| Framework | Pros | Cons | Phù hợp? |
|-----------|------|------|----------|
| **Gradio** | Setup 5 phút, đẹp, có sharing, deploy HuggingFace miễn phí | Ít customize | ✅ Chọn |
| **Streamlit** | Phổ biến, document tốt | Khó deploy free | Backup |
| **Flask + React** | Customize tối đa | Tốn thời gian | ❌ Quá tốn TG |
| **FastAPI + HTML** | Production-ready | UI thô | ❌ |

→ Chọn **Gradio** vì project thiên về demo academic, không phải production. Đặc biệt Gradio có:
- `gr.File` cho upload `.eml`
- `gr.Textbox` cho paste message thẳng
- `gr.Label` cho confidence visualization
- `gr.HTML` cho hiển thị giải thích có format đẹp
- HuggingFace Spaces free hosting

### 3.2 UX Design Principles cho Security Tool

Đọc qua các best practice:
- **Clear visual hierarchy:** Verdict (phishing/safe) phải nổi bật nhất
- **Color semantics:** Đỏ = nguy hiểm, vàng = cẩn thận, xanh = an toàn (universal)
- **Explainability first:** User cần biết *vì sao* bị flag, không chỉ "có/không"
- **Reduce false alarm fatigue:** Hiển thị confidence để user tự quyết định

### 3.3 Integration Patterns

Research các mô hình tích hợp:

**Monolithic:** Tất cả module nằm trong 1 file Python
- Đơn giản, debug dễ
- Khó scale, khó test riêng

**Modular (chọn):** Mỗi module 1 package, expose API qua functions
- Mỗi member làm độc lập
- Test riêng dễ
- Tích hợp qua import + function call

**Microservices:** Mỗi module 1 service, communicate qua HTTP/gRPC
- Production-grade
- Overkill cho academic PoC

→ Chọn **Modular Monolith** — balance giữa đơn giản và clean.

### 3.4 CI/CD cho Academic Project

Setup tối giản:
- GitHub Actions chạy `pytest` mỗi PR
- `black` + `ruff` cho code style
- Pre-commit hooks
- Không cần deploy auto — manual trigger Gradio launch

## 4. Thiết kế

### 4.1 UI Wireframe

```
┌──────────────────────────────────────────────────────────┐
│  🛡️ Phishing Detector — Powered by Gemini LLM            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [Tab 1: Single Analyze]  [Tab 2: Batch]  [Tab 3: Stats]│
│  ──────────────────────                                  │
│                                                          │
│  Choose input mode:                                      │
│  ( ) Paste text  ( ) Upload .eml  ( ) URL only           │
│                                                          │
│  Strategy: [Zero-shot ▼] [Few-shot] [CoT (recommended)]  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Paste your email/SMS here...                     │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│              [ Analyze ]                                 │
│  ────────────────────────────────────────────────        │
│  📊 RESULT                                               │
│                                                          │
│  Verdict: ⚠️  PHISHING (87% confidence)                  │
│                                                          │
│  Red flags detected:                                     │
│  • Urgency tactic: "account suspended in 24h"            │
│  • Suspicious URL: paypa1-secure.com                     │
│  • Mismatch From and Reply-To                            │
│                                                          │
│  Recommendation: 🚫 Do not click any links               │
│                                                          │
│  ▶ Show reasoning steps (if CoT)                         │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Integration Architecture

```python
# app.py (M4 — orchestrator)

import gradio as gr
from data import ingestion, preprocessing   # M1
from llm_core import client                  # M2
from evaluation import metrics               # M3

llm = client.LLMClient()

def analyze_pipeline(input_text: str, strategy: str) -> dict:
    """End-to-end pipeline orchestrating M1 → M2 → output."""
    # M1
    raw = {"type": "text", "raw_content": input_text}
    preprocessed = preprocessing.process(raw)
    
    # M2
    result = llm.analyze(preprocessed, strategy=strategy)
    
    # Format for UI (M4 responsibility)
    return format_result(result)

def format_result(result: dict) -> tuple:
    """Convert result dict to Gradio components."""
    verdict_emoji = {"phishing": "⚠️", "safe": "✅", "suspect": "🟡"}
    label = f"{verdict_emoji[result['label']]} {result['label'].upper()}"
    confidence = result['confidence']
    flags_html = "<ul>" + "".join(f"<li>{f}</li>" for f in result['red_flags']) + "</ul>"
    return label, confidence, flags_html

# Gradio interface
with gr.Blocks(title="Phishing Detector") as demo:
    with gr.Tab("Single Analyze"):
        with gr.Row():
            input_text = gr.Textbox(lines=10, label="Email / SMS content")
            strategy = gr.Radio(["zero_shot", "few_shot", "cot"], 
                                value="cot", label="LLM Strategy")
        analyze_btn = gr.Button("Analyze", variant="primary")
        verdict = gr.Label(label="Verdict")
        confidence = gr.Slider(0, 1, label="Confidence", interactive=False)
        flags = gr.HTML(label="Red flags")
        analyze_btn.click(analyze_pipeline, 
                          inputs=[input_text, strategy],
                          outputs=[verdict, confidence, flags])
    
    with gr.Tab("Batch Mode"):
        # Upload CSV, return CSV with predictions
        pass
    
    with gr.Tab("Performance Stats"):
        # Show metrics chart from M3
        pass

demo.launch()
```

### 4.3 Project Skeleton (đã setup)

```
phishing-detector/
├── data/                # M1
├── llm_core/            # M2
├── evaluation/          # M3
├── ui/
│   └── app.py           # M4
├── tests/
├── .github/
│   └── workflows/ci.yml
├── requirements.txt
├── README.md
└── .env.example
```

## 5. Tiến độ tuần 14

### 5.1 Đã hoàn thành

- ✅ Setup GitHub repo, invite members
- ✅ Setup branch protection, PR template
- ✅ Tạo skeleton project (tất cả folders + `__init__.py`)
- ✅ Viết `requirements.txt` v1
- ✅ Setup GitHub Actions CI (chạy pytest + ruff)
- ✅ Viết draft README với hướng dẫn setup
- ✅ Wireframe UI trên Figma (link trong repo)
- ✅ Prototype Gradio chạy với mock data

### 5.2 Đang làm

- 🔄 Tích hợp module M1 thật (đang chờ M1 hoàn thiện interface)
- 🔄 Style CSS cho Gradio (custom theme)

### 5.3 Demo screenshot (mock)

Đã có 1 prototype chạy với mock LLM (return hardcoded result) để demo flow UI. Khi M2 hoàn thiện sẽ swap mock → real client.

## 6. Vai trò Integration

Ngoài code UI, tôi còn chịu trách nhiệm:

**Cuộc họp nhóm:**
- Lên agenda, take note biên bản
- Đảm bảo deadline từng người
- Mediate khi có conflict về API design

**Code review:**
- Review tất cả PR vào main branch
- Đảm bảo style nhất quán

**Documentation:**
- Maintain README, CONTRIBUTING.md
- Update folder structure khi có thay đổi

**Demo prep:**
- Tuần 16 quay video demo
- Chuẩn bị slide nếu cần present

## 7. Khó khăn

| Vấn đề | Cách xử lý |
|--------|------------|
| Module M1/M2 chưa xong → khó test integration | Dùng mock object theo interface contract đã chốt |
| Gradio CSS hạn chế | Inject custom CSS qua `gr.Blocks(css=...)` |
| 4 người làm song song dễ conflict | Branch theo tên member, merge theo lịch |
| Env management (API keys) | `.env` + `python-dotenv`, KHÔNG commit |

## 8. Kế hoạch tuần 15

- Tích hợp module M1 thật (preprocessing chạy thật)
- Add Tab "Batch Mode" cho upload CSV
- Add Tab "Stats" hiển thị metrics từ M3
- Style UI hoàn chỉnh (theme, logo, color)
- Setup deploy lên HuggingFace Spaces
- Quay video demo nháp

## 9. Tham khảo

1. Abid, A. et al. (2019). *Gradio: Hassle-Free Sharing and Testing of ML Models in the Wild*. ICML AI for Social Good Workshop.
2. Nielsen, J. (1994). *10 Usability Heuristics for User Interface Design*. Nielsen Norman Group.
3. HuggingFace. *Spaces Documentation*. https://huggingface.co/docs/hub/spaces
4. Fowler, M. (2015). *Microservices vs Monolithic Architecture*. https://martinfowler.com/microservices

---
*Số trang ước tính: 5-6 trang khi format chuẩn A4, 1.5 line spacing.*
