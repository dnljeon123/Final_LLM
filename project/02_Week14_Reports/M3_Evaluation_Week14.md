# BÁO CÁO CÁ NHÂN — TUẦN 14
**Member 3 — Evaluation & Metrics**

> *Họ tên:* [Điền tên]
> *MSSV:* [Điền MSSV]
> *Nhóm:* [Số nhóm]
> *Đề tài:* Phishing Detection using LLM
> *Vai trò:* Evaluation Framework & Performance Analysis

---

## 1. Giới thiệu

Trong project phát hiện phishing bằng LLM của nhóm, tôi đảm nhận vai trò **đánh giá hiệu năng**. Đây là vai trò then chốt vì project có yếu tố nghiên cứu (so sánh 3 chiến lược prompting), nên một framework đánh giá khắt khe và đáng tin cậy là điều kiện bắt buộc để rút ra kết luận có giá trị khoa học.

## 2. Vai trò trong tổng thể hệ thống

Module Evaluation của tôi là **nhánh ngang** với main pipeline:
- **Input:** predictions từ M2 + ground truth từ M1
- **Output:** Báo cáo metrics, biểu đồ, error analysis
- **Mục tiêu:** Cho phép so sánh khách quan giữa 3 strategies (ZS/FS/CoT) và phát hiện điểm yếu của hệ thống

Module này quyết định nhóm có thể "tuyên bố" chiến lược nào tốt hơn — nền tảng cho phần Discussion của báo cáo cuối.

## 3. Research

### 3.1 Metrics cho bài toán Classification

Sau khi nghiên cứu, tôi chọn các metrics sau:

**Tại sao không chỉ dùng Accuracy?**
- Dataset có thể imbalance (ví dụ 90% safe, 10% phishing)
- Một classifier "ngu" luôn predict "safe" sẽ đạt accuracy 90% nhưng vô dụng
- Cần precision/recall để hiểu hệ thống thực sự bắt được phishing không

**Bộ metrics đầy đủ:**

| Metric | Công thức | Ý nghĩa với phishing |
|--------|-----------|----------------------|
| Accuracy | (TP+TN)/(TP+TN+FP+FN) | Tỷ lệ đúng tổng thể |
| Precision | TP/(TP+FP) | Trong số bị flag, bao nhiêu đúng → giảm false alarm |
| Recall | TP/(TP+FN) | Trong số phishing thực, bắt được bao nhiêu → giảm bỏ sót |
| F1-score | 2·P·R/(P+R) | Cân bằng P và R |
| ROC-AUC | Diện tích dưới ROC curve | Khả năng phân biệt khi varying threshold |

**Đặc thù phishing:**
- **False Negative tốn hơn False Positive** rất nhiều (bỏ sót phishing → user bị hack vs. flag nhầm email an toàn → user khó chịu)
- → Recall quan trọng hơn Precision
- → Có thể dùng F2-score (weighted F1 với β=2, ưu tiên Recall)

### 3.2 Đánh giá định tính

Ngoài số, cần đánh giá định tính:
- **Explanation quality:** LLM giải thích đúng red flags không?
- **Confidence calibration:** Khi LLM nói "0.9 confidence" thì có thật sự đúng 90% không?
- **Failure modes:** Các loại lỗi LLM hay mắc

### 3.3 Statistical Significance

Để kết luận "CoT tốt hơn Zero-shot" có ý nghĩa khoa học:
- **McNemar's test:** So sánh 2 classifier trên cùng test set
- **Bootstrap confidence interval:** Ước lượng độ tin cậy của metric
- **Multiple runs:** Chạy mỗi strategy nhiều lần (LLM có tính ngẫu nhiên do temperature)

### 3.4 Khảo sát phương pháp benchmark trong literature

| Paper | Dataset | Metric chính |
|-------|---------|--------------|
| Chataut et al. (2024) — LLM for Phishing | 1500 emails | F1, AUC |
| Heiding et al. (2023) — GPT-4 phishing | 3 LLMs compared | Acc, click-through |
| Koide et al. (2023) — ChatGPT detect URL | URL classification | TPR, FPR |

→ Phương pháp của nhóm tôi tương đồng nhưng có điểm mới: so sánh 3 prompting strategies thay vì 3 models.

## 4. Thiết kế Evaluation Framework

### 4.1 Test Set Design

**Composition (mục tiêu):**

| Class | Email | SMS | Total |
|-------|-------|-----|-------|
| Phishing | 200 | 100 | 300 |
| Safe | 200 | 100 | 300 |
| **Total** | **400** | **200** | **600** |

**Lý do balanced 50/50:**
- Mặc dù phishing rate thực tế chỉ ~1-5%, một balanced test set giúp metrics đo lường ổn định hơn
- Nếu cần, có thể reweight để mô phỏng real-world distribution

**Sampling strategy:**
- Stratified random sampling theo nguồn dataset
- Đảm bảo diversity về thời gian (2010-2024) và loại attack

### 4.2 Evaluation Pipeline

```python
def run_evaluation(strategy: str, test_set: list[dict]) -> dict:
    predictions = []
    ground_truth = []
    latencies = []
    
    for sample in test_set:
        start = time.time()
        result = llm_core.analyze(sample, strategy=strategy)
        latency = time.time() - start
        
        predictions.append(result["label"])
        ground_truth.append(sample["ground_truth"])
        latencies.append(latency)
    
    return {
        "accuracy": accuracy_score(ground_truth, predictions),
        "precision": precision_score(ground_truth, predictions, pos_label="phishing"),
        "recall": recall_score(ground_truth, predictions, pos_label="phishing"),
        "f1": f1_score(ground_truth, predictions, pos_label="phishing"),
        "f2": fbeta_score(ground_truth, predictions, beta=2, pos_label="phishing"),
        "confusion_matrix": confusion_matrix(ground_truth, predictions),
        "avg_latency_ms": np.mean(latencies) * 1000,
        "p95_latency_ms": np.percentile(latencies, 95) * 1000
    }
```

### 4.3 Visualization Plan

- Bar chart so sánh 3 strategies × 5 metrics
- Confusion matrix heatmap cho mỗi strategy
- ROC curve overlay
- Latency distribution boxplot
- Confidence calibration plot (reliability diagram)

### 4.4 Error Analysis Protocol

Sau khi chạy, sample 20 FP + 20 FN từ chiến lược tốt nhất để phân tích thủ công:
- Phân loại nguyên nhân (ambiguous, prompt injection, language issue, etc.)
- Đề xuất improvement
- Tạo bảng failure taxonomy

## 5. Tiến độ tuần 14

### 5.1 Đã hoàn thành

- ✅ Khảo sát literature về metrics cho phishing detection
- ✅ Viết module `metrics.py` với các hàm metric chuẩn
- ✅ Skeleton của `runner.py`
- ✅ Mock test với 10 samples giả → pipeline chạy đúng

### 5.2 Đang làm

- 🔄 Phối hợp với M1 để chuẩn bị test set 600 mẫu
- 🔄 Viết visualization module (matplotlib + seaborn)
- 🔄 Setup MLflow để track experiments

### 5.3 Code snippet

```python
def compute_metrics(y_true, y_pred, pos_label="phishing"):
    """Compute full metric suite for phishing detection."""
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=pos_label),
        "recall": recall_score(y_true, y_pred, pos_label=pos_label),
        "f1": f1_score(y_true, y_pred, pos_label=pos_label),
        "f2": fbeta_score(y_true, y_pred, beta=2, pos_label=pos_label),
        "confusion": confusion_matrix(y_true, y_pred).tolist()
    }
```

## 6. Thách thức

| Vấn đề | Cách xử lý |
|--------|------------|
| LLM cho ra kết quả khác nhau giữa các lần chạy | Set `temperature=0`, chạy 3 lần lấy trung bình |
| Tốn nhiều API call để test (600×3 = 1800 calls) | Cache response, dùng async batch |
| Class "suspect" làm metric phức tạp (3 classes) | Quy về binary: suspect → phishing trong eval cuối |
| Subjective: làm sao đánh giá "explanation quality"? | Đánh giá thủ công 30 sample, có rubric chấm |

## 7. Kế hoạch tuần 15

- Hoàn thiện test set 600 mẫu (phối hợp với M1)
- Chạy full evaluation cho cả 3 strategies
- Viết script visualization
- Phân tích confidence calibration
- Triển khai McNemar test cho statistical significance
- Document API cho M4 (UI có thể gọi để show metrics)

## 8. Tham khảo

1. Powers, D. (2011). *Evaluation: From Precision, Recall and F-Measure to ROC, Informedness, Markedness and Correlation*. Journal of ML Technologies.
2. Chataut, R. et al. (2024). *Can AI Keep You Safe? A Study of LLM Performance in Phishing Detection*. IEEE.
3. Heiding, F. et al. (2023). *Devising and Detecting Phishing: LLMs vs. Smaller Human Models*. arXiv:2308.12287.
4. Koide, T. et al. (2023). *Detecting Phishing Sites Using ChatGPT*. arXiv:2306.05816.
5. Saito, T. & Rehmsmeier, M. (2015). *The Precision-Recall Plot Is More Informative than the ROC Plot when Evaluating Binary Classifiers on Imbalanced Datasets*. PLoS ONE.

---
*Số trang ước tính: 5-6 trang khi format chuẩn A4, 1.5 line spacing.*
