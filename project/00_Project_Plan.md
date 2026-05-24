# KẾ HOẠCH TỔNG THỂ — LLM CYBERSECURITY TERM PROJECT

## Tên đề tài
**Phishing Detection System using Large Language Models — A Comparative Study of Prompt Engineering Techniques**

(Hệ thống phát hiện phishing bằng LLM — Nghiên cứu so sánh các kỹ thuật Prompt Engineering)

---

## 1. Vấn đề giải quyết

Tấn công phishing là một trong những mối đe dọa lớn nhất với cá nhân và doanh nghiệp. Các giải pháp truyền thống (rule-based filter, ML classifier truyền thống) gặp khó khăn khi:
- Attacker liên tục thay đổi mẫu (zero-day phishing)
- Không giải thích được vì sao một email bị flag
- Phụ thuộc vào dataset training cũ

**LLM mang lại ưu thế mới:**
- Hiểu ngữ cảnh ngôn ngữ tự nhiên tốt
- Có thể giải thích quyết định (explainability)
- Generalize tốt với các mẫu mới chưa từng thấy

**Mục tiêu PoC:**
Xây dựng hệ thống dùng LLM (Gemini) phân loại email/tin nhắn thành: **phishing / suspect / safe**, kèm giải thích red flags. So sánh 3 kỹ thuật prompting: Zero-shot, Few-shot, Chain-of-Thought.

---

## 2. Phân chia công việc

| Member | Vai trò | Module phụ trách | Deliverable cá nhân |
|--------|---------|------------------|---------------------|
| **M1** | Data Engineer | Data ingestion + Preprocessing | Pipeline xử lý dataset, parser email/SMS |
| **M2** | LLM Engineer | LLM Core + Prompt Engineering | 3 prompt templates, API client, RAG (nếu kịp) |
| **M3** | ML Evaluator | Evaluation + Metrics | Test harness, metrics report, error analysis |
| **M4** | Full-stack | UI + Integration | Gradio demo, kết nối các module, deploy |

**Nguyên tắc:**
- Mỗi người là OWNER của module mình, phải trả lời được mọi câu hỏi về nó
- Họp nhóm 2 buổi/tuần (1 sync + 1 review)
- Code chung trên GitHub, branch theo tên (`feat/m1-preprocessing`, `feat/m2-llm-core`, ...)

---

## 3. Timeline chi tiết (3 tuần)

### TUẦN 14 — Foundation + Research

**Tất cả nhóm (chung):**
- Setup GitHub repo, environment, Gemini API key
- Họp chốt scope, dataset, kiến trúc

**M1 — Data:**
- Tải dataset: Nazario Phishing Corpus, Enron Email, SMS Spam UCI
- Viết script parse `.eml`, trích header/body/URL
- Tạo unified data format (JSON schema)

**M2 — LLM:**
- Đăng ký Gemini API, test gọi cơ bản
- Viết 3 prompt templates (Zero-shot, Few-shot, CoT)
- Output JSON parser

**M3 — Eval:**
- Research metrics: accuracy, precision, recall, F1, confusion matrix
- Tạo bộ test set cân bằng (~200 mẫu phishing, ~200 safe)
- Viết test harness skeleton

**M4 — UI:**
- Research Gradio
- Tạo wireframe UI
- Setup project skeleton, CI/CD (GitHub Actions)

**Báo cáo cá nhân tuần 14:** 3-6 trang/người về module của mình (xem template trong thư mục `02_Week14_Reports/`)

---

### TUẦN 15 — Implementation + Experiment

**M1:** Hoàn thiện preprocessing pipeline, có unit test
**M2:** Tích hợp 3 prompting strategies, đo latency/cost; thử thêm RAG với FAISS
**M3:** Chạy experiment so sánh 3 strategies, lập bảng kết quả + biểu đồ
**M4:** UI Gradio chạy được end-to-end với 1 module mẫu

**Báo cáo cá nhân tuần 15:** 3-6 trang/người về tiến độ + kết quả thực nghiệm

---

### TUẦN 16 — Integration + Polish + Final Report

**Đầu tuần (T2-T4):**
- Integration toàn hệ thống
- Bug fixing, optimize prompt
- Chạy final experiment trên test set lớn

**Cuối tuần (T5-CN):**
- Viết báo cáo nhóm (mỗi người viết section của mình rồi gộp)
- Quay video demo
- Chuẩn bị slide thuyết trình (nếu cần)

**Deliverable:**
- Báo cáo nhóm (15-25 trang)
- PoC chạy được (GitHub repo + Gradio demo)
- Video demo 3-5 phút

---

## 4. Tech Stack

| Layer | Tool | Lý do |
|-------|------|-------|
| Language | Python 3.10+ | Standard cho AI/ML |
| LLM API | Google Gemini 1.5 Flash | Free tier rộng, đủ nhanh |
| Email parsing | `email`, `mailparser` | Built-in + robust |
| Vector DB | FAISS | Local, free, đủ cho PoC |
| Embedding | `sentence-transformers` | Free, chạy local |
| UI | Gradio | Đơn giản, đẹp, deploy nhanh |
| Metrics | scikit-learn, pandas, matplotlib | Standard |
| Version control | GitHub | Standard |
| Documentation | Markdown + Mermaid | Dễ render |

---

## 5. Tiêu chí Outstanding (O)

Để đạt Outstanding, nhóm cần thể hiện:

✅ **Originality:** So sánh 3 prompting strategies là điểm nghiên cứu (không chỉ "gọi API rồi xong")
✅ **Technical depth:** Tích hợp RAG, đo cost/latency, error analysis chi tiết
✅ **Reproducibility:** Code chạy được trên máy người khác, có README rõ ràng
✅ **Evaluation rigor:** Metrics đầy đủ, có confusion matrix, có ví dụ failure case
✅ **Real-world relevance:** Dataset thực, không phải toy data
✅ **Documentation:** Báo cáo đầy đủ, có hình minh họa, citation đầy đủ
✅ **Demo:** UI chạy được, có video demo

---

## 6. Rủi ro & Cách xử lý

| Rủi ro | Khả năng | Cách xử lý |
|--------|----------|------------|
| Gemini API hết quota | Trung bình | Mỗi member 1 API key riêng, có fallback OpenRouter |
| Member nghỉ giữa chừng | Thấp | Code modular, có thể tiếp quản |
| Dataset không cân bằng | Cao | Stratified sampling, class weight |
| LLM hallucination | Cao | JSON schema enforcement, retry logic |
| Tích hợp trễ | Trung bình | Mỗi module có mock interface, test độc lập trước |

---

## 7. Quy tắc làm việc

1. **Commit message rõ ràng:** `feat(m1): add email header parser`
2. **PR review chéo:** Mỗi PR cần ít nhất 1 approval
3. **Báo cáo cá nhân KHÔNG copy nhau** — nội dung phải khác nhau theo module
4. **Họp đúng giờ, có biên bản** — Member 4 ghi lại
5. **Code có docstring + type hints**
6. **Test coverage tối thiểu 60%**

---

## 8. Liên kết tài liệu

- `01_Architecture.md` — Kiến trúc chi tiết
- `02_Week14_Reports/` — Template báo cáo tuần 14 (4 files)
- `03_Week15_Reports/` — Template báo cáo tuần 15 (4 files)
- `04_Final_Report_Template.md` — Khung báo cáo nhóm
- `05_PoC_Code/` — Code PoC
