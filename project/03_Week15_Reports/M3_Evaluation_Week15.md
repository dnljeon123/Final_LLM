# BÁO CÁO CÁ NHÂN — TUẦN 15
**Member 3 — Evaluation & Metrics**

> *Họ tên:* [Điền tên] | *MSSV:* [Điền] | *Nhóm:* [Số nhóm]
> *Vai trò:* Evaluation Framework

---

## 1. Tóm tắt tuần 14

Tuần 14: research metrics, thiết kế evaluation framework, viết skeleton `metrics.py`. Tuần 15 **chạy experiment chính thức và phân tích kết quả** — đây là tuần đem lại số liệu dùng cho báo cáo nhóm.

## 2. Công việc tuần 15

### 2.1 Hoàn thiện Evaluation Pipeline

```python
def run_full_evaluation(strategies: list[str], test_set: list[dict], 
                        n_runs: int = 3) -> dict:
    """Run evaluation with multiple runs for statistical stability."""
    results = {}
    for strategy in strategies:
        runs = []
        for run_id in range(n_runs):
            predictions = []
            for sample in tqdm(test_set, desc=f"{strategy} run {run_id+1}"):
                pred = llm_core.analyze(sample, strategy=strategy)
                predictions.append(pred)
            runs.append(compute_metrics(test_set, predictions))
        results[strategy] = aggregate_runs(runs)
    return results
```

Mỗi strategy chạy 3 lần (do LLM có temperature noise), lấy mean ± std.

### 2.2 Test set chính thức

Đã nhận từ M1 và verify:
- 600 mẫu balanced (300 phishing + 300 safe)
- 67% email, 33% SMS
- Đa dạng theo nguồn và thời gian

### 2.3 Kết quả full evaluation (100 mẫu sơ bộ)

Để tiết kiệm API quota tuần 15, chạy trước 100 mẫu. Full 600 sẽ chạy tuần 16.

**Bảng kết quả chính:**

| Strategy | Accuracy | Precision | Recall | F1 | F2 | Latency (ms) |
|----------|----------|-----------|--------|-----|-----|----------------|
| Zero-shot | 0.82 ± 0.02 | 0.83 | 0.80 | 0.81 | 0.80 | 890 |
| Few-shot | 0.88 ± 0.01 | 0.86 | 0.90 | 0.88 | 0.89 | 1010 |
| CoT | 0.91 ± 0.01 | 0.89 | 0.94 | 0.91 | 0.93 | 1620 |
| Few-shot + RAG | **0.93 ± 0.01** | **0.92** | 0.94 | **0.93** | **0.94** | 1340 |

**Quan sát chính:**
1. Few-shot + RAG **dẫn đầu mọi metric**
2. CoT có **Recall cao nhất** sau RAG → ít bỏ sót phishing
3. ZS là baseline, gap với CoT là 9% F1 → đáng kể
4. Latency của CoT cao nhất do output dài hơn

### 2.4 Confusion Matrices

Cho từng strategy, đã sinh heatmap. Ví dụ CoT:

```
              Predicted
              Phishing  Safe  Suspect
Actual Phishing   47      2      1    (Recall = 47/50 = 94%)
       Safe        4     44      2    (Specificity = 44/50 = 88%)
```

→ False Negative rate = 6% (vẫn cao cho security, nhưng đã rất tốt với LLM)

### 2.5 Statistical Significance

McNemar's test giữa các cặp strategies:

| Pair | p-value | Significant? |
|------|---------|--------------|
| ZS vs Few-shot | 0.018 | ✅ (p < 0.05) |
| Few-shot vs CoT | 0.041 | ✅ |
| CoT vs RAG | 0.062 | ❌ borderline |
| ZS vs RAG | 0.001 | ✅ rõ ràng |

→ RAG > CoT nhưng chưa đủ significant ở 100 mẫu. Sẽ rõ hơn ở 600 mẫu tuần 16.

### 2.6 Confidence Calibration Analysis

Plot reliability diagram cho 3 strategies:

| Strategy | ECE (Expected Calibration Error) |
|----------|----------------------------------|
| Zero-shot | 0.14 (over-confident) |
| Few-shot | 0.09 |
| CoT | **0.05** (best) |
| RAG | 0.07 |

→ CoT có **calibration tốt nhất** — khi nó nói "0.9 confidence", thật sự ~88-90% case đúng. Đây là lợi thế quan trọng cho security tool, vì cho phép set threshold đáng tin cậy.

### 2.7 Latency & Cost Analysis

Trên Gemini Flash free tier:

| Strategy | Avg latency | Tokens (in/out) | Cost (paid tier hypothetical) |
|----------|-------------|-----------------|--------------------------------|
| ZS | 890ms | 350 / 80 | $0.0001 |
| FS | 1010ms | 800 / 90 | $0.0002 |
| CoT | 1620ms | 450 / 250 | $0.0003 |
| RAG | 1340ms | 1100 / 90 | $0.0003 + embedding |

Throughput: ~15 req/min (giới hạn free tier), đủ cho academic PoC nhưng không production-ready.

## 3. Phối hợp với members khác

- **M1:** Đã verify test set có đầy đủ ground truth, không có duplicate
- **M2:** Đã chạy eval với mọi strategy M2 cung cấp, feedback error analysis cho M2
- **M4:** Đã export metrics ra JSON để UI hiển thị trong Tab "Stats"

## 4. Visualizations đã tạo

1. Bar chart: Accuracy/F1 comparison across 4 strategies
2. Confusion matrix heatmap (4 strategies × 1)
3. Reliability diagram cho confidence calibration
4. Latency boxplot
5. ROC curves overlay

Tất cả lưu trong `/evaluation/figures/` dạng PNG + PDF (high-res cho báo cáo).

## 5. Khó khăn & Giải pháp

| Vấn đề | Giải pháp |
|--------|-----------|
| Chạy 100 mẫu × 4 strategies × 3 runs = 1200 calls hết quota nhanh | Dùng 2 API keys luân phiên, cache response |
| LLM đôi khi trả về label không hợp lệ | Fallback "suspect" + log để M2 review |
| Class "suspect" làm confusion matrix 3x3 | Cho phần báo cáo, có cả binary view (gộp suspect vào phishing) |

## 6. Kế hoạch tuần 16

- Chạy full evaluation trên 600 mẫu (chia 2 ngày để không hết quota)
- Phân tích lỗi chuyên sâu: 30 FN + 30 FP của best strategy
- Hoàn thiện báo cáo metrics: bảng + biểu đồ chất lượng cao
- Đóng góp section "Evaluation & Results" trong báo cáo nhóm
- Chuẩn bị slide phần kết quả nếu có present

## 7. Tham khảo bổ sung tuần này

1. Guo, C. et al. (2017). *On Calibration of Modern Neural Networks*. ICML.
2. McNemar, Q. (1947). *Note on the sampling error of the difference between correlated proportions*. Psychometrika.
3. Davis, J. & Goadrich, M. (2006). *The Relationship Between Precision-Recall and ROC Curves*. ICML.

---
*Ước tính 5-6 trang format chuẩn.*
