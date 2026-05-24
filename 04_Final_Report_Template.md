# BÁO CÁO NHÓM CUỐI KỲ — TUẦN 16
# Phishing Detection System using Large Language Models
## A Comparative Study of Prompt Engineering Techniques

> **Nhóm:** [Số nhóm]
> **Thành viên:**
> - [Tên M1] — MSSV [...] — Data Engineering
> - [Tên M2] — MSSV [...] — LLM Core
> - [Tên M3] — MSSV [...] — Evaluation
> - [Tên M4] — MSSV [...] — UI & Integration
>
> **GitHub:** [URL repo]
> **Demo:** [URL HuggingFace Spaces]
> **Video:** [URL video demo]

---

## TÓM TẮT (ABSTRACT)

> *Người viết: M2 + M3, ~150-200 từ*

Bài báo cáo này trình bày một hệ thống phát hiện phishing dựa trên Large Language Models (LLMs). Mục tiêu nghiên cứu chính: so sánh hiệu năng của 3 chiến lược prompt engineering (Zero-shot, Few-shot, Chain-of-Thought) và một biến thể Retrieval-Augmented Generation (RAG) trên bài toán phân loại nhị phân phishing/safe. Trên test set 600 mẫu (bao gồm email từ Nazario Corpus và SMS từ UCI Dataset), Few-shot + RAG đạt F1-score [XX], vượt baseline Zero-shot [YY] điểm phần trăm. Chain-of-Thought đặc biệt cho ra confidence calibration tốt nhất (ECE = 0.05). Hệ thống còn cung cấp explainability — liệt kê các red flags cụ thể giúp người dùng hiểu lý do flag, đây là lợi thế lớn so với các classifier truyền thống. PoC được triển khai qua giao diện Gradio, deploy công khai trên HuggingFace Spaces.

**Keywords:** Phishing detection, Large Language Models, Prompt engineering, Cybersecurity, Explainable AI

---

## 1. GIỚI THIỆU

> *Người viết: M2, ~1 trang*

### 1.1 Bối cảnh
- Số liệu thống kê phishing 2024-2025 (cite APWG)
- Thiệt hại kinh tế
- Tốc độ phát triển của LLM trong NLP

### 1.2 Hạn chế của giải pháp truyền thống
- Rule-based: dễ bị bypass
- ML cổ điển: cần feature engineering, không generalize
- Deep learning: cần data lớn

### 1.3 Đóng góp của project
1. Xây dựng PoC phishing detection dùng LLM end-to-end
2. So sánh có hệ thống 3+1 prompting strategies trên cùng test set
3. Phân tích confidence calibration — yếu tố quan trọng cho security tool
4. Đưa explainability vào output — red flags + reasoning

### 1.4 Cấu trúc báo cáo
[Outline các section còn lại]

---

## 2. RELATED WORK / CƠ SỞ LÝ THUYẾT

> *Người viết: M2, ~2 trang*

### 2.1 Phishing Detection — Tổng quan
- Lịch sử (Almomani 2013, APWG reports)
- Các approach: rule, ML, DL

### 2.2 Large Language Models
- Transformer architecture (Vaswani 2017)
- Pretrained models (GPT, Gemini, Claude)
- Khả năng zero-shot và few-shot

### 2.3 Prompt Engineering
- Zero-shot (Brown 2020)
- Few-shot (Brown 2020)
- Chain-of-Thought (Wei 2022)
- Self-consistency, Tree-of-Thought (mention briefly)

### 2.4 RAG (Retrieval-Augmented Generation)
- Lewis 2020
- Ứng dụng trong domain-specific tasks

### 2.5 LLM trong Cybersecurity
- Heiding 2023, Chataut 2024, Koide 2023
- Identify gap → opportunity cho nhóm

---

## 3. KIẾN TRÚC HỆ THỐNG

> *Người viết: M4 + M1, ~2 trang*

### 3.1 Tổng quan kiến trúc 4 tầng
[Insert architecture diagram]

### 3.2 Tầng Data Ingestion
[M1 viết, tóm tắt từ báo cáo cá nhân]

### 3.3 Tầng Preprocessing
[M1 viết]

### 3.4 Tầng LLM Core
[M2 viết]

### 3.5 Tầng Decision & Output
[M4 viết]

### 3.6 Interface Contracts
[M4 viết, code snippets API]

---

## 4. PHƯƠNG PHÁP

> *Người viết: M2, ~3 trang*

### 4.1 3 Prompting Strategies

#### 4.1.1 Zero-shot Prompting
[Prompt template, ưu/nhược]

#### 4.1.2 Few-shot Prompting
[Prompt template, cách chọn examples]

#### 4.1.3 Chain-of-Thought Prompting
[Prompt template với 6 steps]

### 4.2 RAG Augmentation
- FAISS index
- sentence-transformers embedding
- Dynamic few-shot example selection

### 4.3 JSON Schema Enforcement
[Pydantic schema, validation]

### 4.4 Error Handling
[Retry, rate limit, fallback]

---

## 5. THỰC NGHIỆM

> *Người viết: M3, ~3-4 trang*

### 5.1 Dataset

| Source | Type | Phishing | Safe | Total |
|--------|------|----------|------|-------|
| Nazario | Email | 200 | — | 200 |
| Enron Sent | Email | — | 200 | 200 |
| UCI SMS Spam | SMS | 100 | 100 | 200 |
| **Total** | | **300** | **300** | **600** |

### 5.2 Experimental Setup
- LLM: Gemini 1.5 Flash
- Temperature: 0 (deterministic)
- 3 runs per strategy → mean ± std
- Hardware: [specs]

### 5.3 Metrics
[Định nghĩa accuracy, precision, recall, F1, F2, ECE]

### 5.4 Kết quả chính

**Bảng 1: Performance comparison**

| Strategy | Accuracy | Precision | Recall | F1 | F2 | Latency (ms) |
|----------|----------|-----------|--------|-----|-----|--------------|
| Zero-shot | [X] | [X] | [X] | [X] | [X] | [X] |
| Few-shot | [X] | [X] | [X] | [X] | [X] | [X] |
| CoT | [X] | [X] | [X] | [X] | [X] | [X] |
| FS + RAG | **[X]** | **[X]** | **[X]** | **[X]** | **[X]** | [X] |

[Insert Figure 1: Bar chart comparison]

### 5.5 Confusion Matrices
[Insert Figure 2: 2x2 grid of confusion matrices]

### 5.6 Confidence Calibration
[Insert Figure 3: Reliability diagrams]
[ECE values bảng]

### 5.7 Statistical Significance
[McNemar test results]

### 5.8 Error Analysis
[Phân loại 30 FP + 30 FN, taxonomy of errors]

---

## 6. DISCUSSION

> *Người viết: M2 + M3, ~1.5 trang*

### 6.1 Vì sao Few-shot + RAG thắng?
- Dynamic context, relevant examples
- Reduce hallucination

### 6.2 Trade-off Latency vs Accuracy
- CoT chậm nhưng calibration tốt
- RAG nhanh hơn CoT nhưng cần infrastructure

### 6.3 Vì sao CoT có calibration tốt nhất?
- Reasoning forces model to be more deliberate

### 6.4 Hạn chế
- Phụ thuộc API → cost, rate limit
- Latency không phù hợp real-time email server
- Vẫn còn FN cho sophisticated spear phishing
- Dataset chủ yếu English

---

## 7. ỨNG DỤNG THỰC TIỄN (PoC Demo)

> *Người viết: M4, ~1.5 trang*

### 7.1 Giao diện
[Screenshots UI]

### 7.2 Use cases
- Single email analysis
- Batch processing
- Performance monitoring

### 7.3 Deployment
- HuggingFace Spaces
- CI/CD pipeline

---

## 8. KẾT LUẬN & HƯỚNG PHÁT TRIỂN

> *Người viết: Cả nhóm, M2 chủ trì, ~1 trang*

### 8.1 Kết luận
- Tóm tắt key findings
- LLM khả thi cho phishing detection
- Prompt engineering matters

### 8.2 Hướng phát triển
- Fine-tune model riêng cho phishing
- Multi-modal (xử lý ảnh logo giả)
- Multilingual
- Realtime integration với mail server (Outlook plugin)
- Adversarial robustness (chống prompt injection)

---

## TÀI LIỆU THAM KHẢO

> *Người tổng hợp: M3*

[Hợp nhất citation từ 4 báo cáo cá nhân, format APA hoặc IEEE]

---

## PHỤ LỤC

### A. Code structure & file mapping
### B. Sample LLM prompts đầy đủ
### C. Failure case examples
### D. Phân công công việc chi tiết theo deliverable

---

## PHÂN CÔNG VIẾT BÁO CÁO

| Section | Người viết chính | Reviewer |
|---------|------------------|----------|
| Abstract | M2 + M3 | All |
| 1. Giới thiệu | M2 | M3 |
| 2. Related Work | M2 | M3 |
| 3. Kiến trúc | M4 + M1 | M2 |
| 4. Phương pháp | M2 | M3 |
| 5. Thực nghiệm | M3 | M2 |
| 6. Discussion | M2 + M3 | M1, M4 |
| 7. Demo | M4 | M1 |
| 8. Kết luận | All | M2 |
| References | M3 | M2 |

**Quy trình:**
1. Mỗi người viết section của mình (Tuần 16, ngày 1-3)
2. Cross-review (Ngày 4-5)
3. Merge + edit chung (Ngày 6)
4. Final review + submit (Ngày 7)

**Format yêu cầu:**
- A4, 1.5 spacing, Times New Roman 13pt
- Heading: bold, đánh số
- Hình + bảng: có caption, đánh số
- Citation: IEEE style
- Tổng: 20-25 trang (không kể phụ lục)

---

*Tip để đạt Outstanding (O):*
> - Số liệu và biểu đồ phải đẹp, chuyên nghiệp
> - Mọi claim phải có evidence (số hoặc citation)
> - Discussion phải sâu, không chỉ liệt kê kết quả
> - Demo phải chạy mượt, có video backup nếu wifi gặp sự cố
> - Code repo phải organized, có README chi tiết
> - Nộp đúng deadline + check format kỹ
