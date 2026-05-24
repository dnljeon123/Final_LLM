# BÁO CÁO CÁ NHÂN — TUẦN 15
**Member 4 — UI & System Integration**

> *Họ tên:* [Điền tên] | *MSSV:* [Điền] | *Nhóm:* [Số nhóm]
> *Vai trò:* Frontend & Integration

---

## 1. Tóm tắt tuần 14

Tuần 14: setup repo, CI/CD, skeleton Gradio app với mock data, wireframe UI. Tuần 15 **tích hợp module thật + hoàn thiện UI 3 tabs + deploy lên HuggingFace Spaces**.

## 2. Công việc tuần 15

### 2.1 Integration với module thật

Đã tích hợp thành công:
- **M1 (Preprocessing):** UI gọi được `data.preprocessing.process(raw)` qua import trực tiếp
- **M2 (LLM Core):** `LLMClient.analyze(message, strategy)` trả về JSON đầy đủ
- **M3 (Metrics):** Load file `metrics_summary.json` từ M3 để render trong Tab Stats

End-to-end flow chạy được: upload `.eml` → preprocess → LLM analyze → render kết quả + giải thích.

### 2.2 UI hoàn chỉnh — 3 Tabs

**Tab 1: Single Analyze**
- Input: paste text hoặc upload `.eml`
- Strategy selector (ZS/FS/CoT/RAG)
- Output: Verdict (color-coded), Confidence slider, Red flags list, Recommendation
- Expandable: CoT reasoning steps

**Tab 2: Batch Mode**
- Upload CSV với cột `message`
- Download CSV có thêm cột `verdict`, `confidence`, `red_flags`
- Progress bar (Gradio `gr.Progress`)
- Process 50 mẫu/batch để không vượt rate limit

**Tab 3: Performance Stats**
- Hiển thị bar chart so sánh 4 strategies (Plotly)
- Confusion matrix heatmap
- Latency boxplot
- Load số liệu từ file M3 export

### 2.3 Custom styling

Đã apply custom CSS:
- Verdict color: đỏ (#dc3545) cho phishing, xanh (#28a745) cho safe, vàng (#ffc107) cho suspect
- Logo và favicon
- Dark mode toggle
- Responsive cho mobile

### 2.4 Deploy lên HuggingFace Spaces

Đã thành công deploy:
- URL: `https://huggingface.co/spaces/[group-name]/phishing-detector`
- Auto-redeploy khi push main branch
- Set Gemini API key qua HF Secrets (không expose)

### 2.5 Code snippet — main app structure

```python
import gradio as gr
from data.preprocessing import process
from llm_core.client import LLMClient
import json

llm = LLMClient()

def analyze_single(input_text, file, strategy):
    raw = input_text if input_text else open(file.name).read()
    preprocessed = process({"type": "auto", "raw_content": raw})
    result = llm.analyze(preprocessed, strategy=strategy)
    
    return (
        format_verdict(result["label"]),
        result["confidence"],
        format_flags_html(result["red_flags"]),
        result.get("reasoning", {})
    )

def batch_analyze(csv_file, strategy, progress=gr.Progress()):
    df = pd.read_csv(csv_file.name)
    results = []
    for i, msg in enumerate(progress.tqdm(df["message"])):
        result = llm.analyze({"cleaned_text": msg}, strategy=strategy)
        results.append(result)
    df["verdict"] = [r["label"] for r in results]
    df["confidence"] = [r["confidence"] for r in results]
    df.to_csv("output.csv", index=False)
    return "output.csv"

with gr.Blocks(theme=gr.themes.Soft(), title="🛡️ Phishing Detector") as app:
    gr.Markdown("# 🛡️ Phishing Detector — Powered by Gemini")
    with gr.Tabs():
        with gr.Tab("Single Analyze"):
            # ... full implementation
            pass
        with gr.Tab("Batch Mode"):
            pass
        with gr.Tab("Performance Stats"):
            pass

app.launch()
```

### 2.6 Code quality

- Reformat toàn repo với `black` (đồng nhất style)
- Linting `ruff` pass 0 errors
- Test coverage tổng: **68%** (mục tiêu 60%)
- README.md đầy đủ: install, run, troubleshoot

### 2.7 Demo video (draft)

Đã quay demo nháp 3 phút:
- Intro vấn đề phishing (30s)
- Demo Single mode với email phishing thật (60s)
- Demo Batch mode (40s)
- Show Stats tab (30s)
- Outro (20s)

Sẽ polish thêm ở tuần 16.

## 3. Quản lý nhóm tuần 15

Tôi đã tổ chức:
- 2 buổi họp sync (T2, T6) — biên bản trong `/docs/meeting-notes/`
- Review 18 PRs (5 từ M1, 7 từ M2, 6 từ M3)
- Update kanban board: 32 tasks done, 8 in progress, 6 backlog

**Conflicts đã giải quyết:**
- M2 và M3 bất đồng về format JSON: thống nhất qua schema doc
- Branch conflict giữa M1 và M3: pair programming 30 phút resolve

## 4. Khó khăn & Giải pháp

| Vấn đề | Giải pháp |
|--------|-----------|
| HF Spaces free tier có 16GB RAM limit | Loại bỏ FAISS index lớn, dùng quantized embeddings |
| Gradio không support custom React component | Workaround bằng HTML inject, đủ cho demo |
| Batch mode bị timeout khi >100 mẫu | Chia chunk 50, progress bar update từng chunk |
| API key bị leak trong commit history | Rotate key, dùng `git-filter-repo` xóa khỏi history |

## 5. Kế hoạch tuần 16

- Polish UI: animation, transitions
- Quay video demo final với chất lượng cao
- Đóng góp section "Implementation & Demo" trong báo cáo nhóm
- Coordinate viết báo cáo nhóm: assign sections, merge final
- Prepare presentation slides nếu cần
- Final smoke test toàn hệ thống

## 6. Tham khảo bổ sung tuần này

1. Gradio team. (2024). *Building ML Demos with Gradio Blocks*. https://www.gradio.app/guides
2. HuggingFace. *Spaces Hardware and Pricing*. https://huggingface.co/pricing
3. Plotly. *Python Graphing Library*. https://plotly.com/python

---
*Ước tính 4-5 trang format chuẩn.*
