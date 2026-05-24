# BÁO CÁO CÁ NHÂN — TUẦN 14
**Member 1 — Data Engineering Module**

> *Họ tên:* [Điền tên]
> *MSSV:* [Điền MSSV]
> *Nhóm:* [Số nhóm]
> *Đề tài:* Phishing Detection using LLM
> *Vai trò:* Data Ingestion & Preprocessing

---

## 1. Giới thiệu

Trong project term này, nhóm chúng tôi xây dựng một hệ thống phát hiện phishing dựa trên Large Language Model (LLM), so sánh hiệu quả của 3 kỹ thuật prompt engineering: Zero-shot, Few-shot, và Chain-of-Thought. Là thành viên phụ trách tầng dữ liệu, báo cáo này trình bày phần research, thiết kế, và tiến độ tuần 14 của module Data Ingestion & Preprocessing.

## 2. Vai trò trong tổng thể hệ thống

Module Data nằm ở tầng 1-2 của kiến trúc 4 tầng, có nhiệm vụ:
1. Nhận input đa dạng (file `.eml`, SMS, URL, batch CSV)
2. Trích xuất features: header, body, URL, attachments
3. Chuẩn hóa output thành JSON schema thống nhất để module LLM (M2) tiêu thụ

Đầu ra của tôi quyết định trực tiếp chất lượng input cho LLM — "garbage in, garbage out" — nên đây là module nền tảng.

## 3. Research

### 3.1 Datasets

Tôi đã khảo sát và chọn 3 datasets chính:

| Dataset | Số mẫu | Loại | Nguồn |
|---------|--------|------|-------|
| Nazario Phishing Corpus | ~5000 | Email phishing thật | monkey.org/~jose/phishing |
| Enron Email Dataset | 500k+ | Email hợp pháp | cs.cmu.edu/~enron |
| UCI SMS Spam | 5574 | SMS spam/phishing | UCI ML Repository |

**Lý do chọn:**
- Nazario: Email phishing thật thu thập từ 2004-2024, đa dạng loại tấn công
- Enron: Email công ty thật, dùng làm "negative samples"
- UCI SMS: Mở rộng sang kênh SMS

### 3.2 Email Header Analysis

Tôi đã research về cấu trúc email theo RFC 5322 và các kỹ thuật phishing thường gặp ở header:

- **From / Reply-To mismatch:** Phishing thường dùng tên hiển thị giả nhưng địa chỉ thật khác
- **Received chain analysis:** Đường đi của email tiết lộ máy chủ gửi
- **SPF/DKIM/DMARC:** Các giao thức xác thực sender
- **Display name spoofing:** "PayPal Support" nhưng email là random@gmail.com

### 3.3 URL Analysis Techniques

- **Homoglyph detection:** `paypa1.com` vs `paypal.com`, `g00gle.com` vs `google.com`
- **Typosquatting:** `paypa1-secure.com`, `amazon-verify.net`
- **URL shortener resolution:** bit.ly, tinyurl che giấu URL thật
- **Subdomain abuse:** `paypal.com.evil.com`

## 4. Thiết kế module

### 4.1 Unified Data Schema

```json
{
  "id": "msg_001",
  "type": "email | sms | url",
  "raw_content": "...",
  "cleaned_text": "...",
  "urls": [
    {
      "url": "http://...",
      "resolved": "...",
      "is_shortened": false,
      "suspicious_indicators": ["homoglyph", "typosquat"]
    }
  ],
  "headers": {
    "from": "...",
    "reply_to": "...",
    "subject": "...",
    "spf_pass": true,
    "from_reply_mismatch": false
  },
  "metadata": {
    "language": "en",
    "char_count": 1234,
    "attachment_count": 0
  },
  "ground_truth": "phishing | safe"
}
```

### 4.2 Pipeline architecture

```
Raw input → Loader → Cleaner → Header Parser → URL Extractor → Metadata → Unified JSON
```

Mỗi bước là một function thuần (pure function), dễ test độc lập.

### 4.3 Tech stack module

- `email` (Python stdlib) — parse email
- `BeautifulSoup4` — strip HTML
- `tldextract` — phân tích domain
- `dnspython` — DNS lookup cho SPF/DMARC
- `langdetect` — phát hiện ngôn ngữ
- `pandas` — quản lý dataset

## 5. Tiến độ tuần 14

### 5.1 Đã hoàn thành

- ✅ Tải về 3 datasets (Nazario, Enron sample, SMS Spam)
- ✅ Viết loader cho file `.eml` (sử dụng `email.parser`)
- ✅ Viết text cleaner: strip HTML, decode quoted-printable
- ✅ Tạo unified JSON schema (xem mục 4.1)
- ✅ Setup folder structure trong GitHub repo

### 5.2 Đang làm

- 🔄 URL extractor với homoglyph detection
- 🔄 Email header parser

### 5.3 Code snippet ví dụ

```python
def load_eml(file_path: str) -> dict:
    """Load .eml file and extract base structure."""
    with open(file_path, 'rb') as f:
        msg = email.message_from_bytes(f.read())
    
    return {
        "id": hashlib.md5(file_path.encode()).hexdigest()[:8],
        "type": "email",
        "raw_content": msg.as_string(),
        "headers": {
            "from": msg.get("From"),
            "reply_to": msg.get("Reply-To"),
            "subject": msg.get("Subject"),
            "received": msg.get_all("Received", [])
        },
        "body": extract_body(msg)
    }
```

## 6. Khó khăn & cách xử lý

| Khó khăn | Cách xử lý |
|----------|------------|
| Encoding hỗn loạn (Windows-1252, UTF-8, Base64) | Dùng `email.policy.default` để auto-detect |
| Email có nhiều part (text + HTML + attachment) | Walk qua `msg.walk()`, ưu tiên text/plain |
| Một số .eml file bị malformed | Try-except, log lỗi, skip mẫu xấu |

## 7. Kế hoạch tuần 15

- Hoàn thiện URL extractor + homoglyph detection
- Viết SPF/DKIM checker (lookup DNS)
- Tạo test set cân bằng (200 phishing + 200 safe)
- Viết unit test (target coverage 70%)
- Document API cho M2/M3/M4 dùng

## 8. Tham khảo

1. Resnick, P. (2008). *RFC 5322 — Internet Message Format*.
2. Kitterman, S. (2014). *RFC 7208 — Sender Policy Framework (SPF)*.
3. Nazario, J. (2024). *Phishing Corpus*. https://monkey.org/~jose/phishing
4. UCI ML Repository. *SMS Spam Collection Dataset*.
5. Klimt, B., & Yang, Y. (2004). *The Enron Corpus*. ECML.

---
*Số trang ước tính: 4-5 trang khi format chuẩn A4, 1.5 line spacing.*
