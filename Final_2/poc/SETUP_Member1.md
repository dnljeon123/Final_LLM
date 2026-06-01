# Hướng dẫn Setup & Sử dụng — Module Data (Member 1)

> Dinh Ngoc Lan (M11415806) — Data Engineer
> Cập nhật: Week 15

Tài liệu này hướng dẫn cách chạy phần preprocessing/data và cách gọi nó từ
module khác (LLM, eval, app).

---

## 1. Cài đặt môi trường

```bash
# Từ thư mục Final_2 (chứa thư mục poc)
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Git Bash):  source venv/Scripts/activate
# macOS/Linux:         source venv/bin/activate

cd poc
pip install -r requirements.txt
```

Module data/ chạy OFFLINE, KHÔNG cần Gemini API key.
(Chỉ phần demo Gradio app.py mới cần key.)

---

## 2. Dữ liệu

Repo KHÔNG chứa CSV thô (kaggle_fishing/) vì quá nặng (>250MB, vượt giới hạn GitHub).

**Tin tốt: bạn KHÔNG cần CSV thô.** File JSON đã xử lý sẵn đã có trong repo:

| File | Nội dung | Dùng khi |
|---|---|---|
| data/samples/demo_samples.json    | 6 email demo            | Test nhanh, chạy app |
| data/samples/kaggle_dataset.json  | 200 mẫu (Week 14)       | Baseline cũ |
| data/samples/kaggle_dataset_v2.json | 1,000 mẫu (Week 15)   | **Dùng cái này** cho eval |

CHỈ KHI muốn tự sinh lại dataset mới: tải CSV từ
https://www.kaggle.com/datasets/subhajournal/phishingemails
giải nén vào kaggle_fishing/, rồi chạy:
```bash
python convert_kaggle_dataset_v2.py
```

---

## 3. Cách gọi module data (cho Member 2 - LLM, Member 3 - eval)

M��i thứ trả về object `Record` thống nhất. Import như sau:

```python
from data import preprocess_text, preprocess, load_samples, stratified_split

# Xử lý 1 email từ text:
rec = preprocess_text("From: a@b.com\nSubject: ...\n\nNội dung email")

# Các field có sẵn trong Record:
rec.clean_text      # nội dung đã làm sạch (đưa cái này cho LLM)
rec.urls            # list URL tìm được
rec.auth_status     # dict {spf: pass, dkim: fail, ...}
rec.subject, rec.sender
rec.label           # 1=phishing, 0=legit, None=chưa gán
rec.llm_input_text()  # CHUỖI gọn đã format sẵn để gửi thẳng cho LLM

# Nạp cả tập 1,000 mẫu Week 15:
import json
from data.preprocessor import preprocess_text
raw = json.load(open("data/samples/kaggle_dataset_v2.json", encoding="utf-8"))
records = [preprocess_text(x["text"], label=x["label"]) for x in raw]

# Chia train/test (giữ tỷ lệ mỗi lớp, seed cố định):
train, test = stratified_split(records, ratio=0.2)
```

LƯU Ý cho Member 3 (eval): hàm stratified_split() đã sẵn sàng, seed=42 cố định
trong config.py. Cần thống nhất tỷ lệ split (mặc định 0.2) trước khi chốt tập eval.

---

## 4. Chạy thử / kiểm tra

```bash
# Chạy toàn bộ test (basic + edge cases):
pytest tests/ -v
# Mong đợi: test_basic (17) + test_edge_cases (24) đều pass

# Chạy lại thí nghiệm Week 15 (in số liệu ra màn hình):
python member1_experiments_week15.py

# Vẽ lại 5 chart Week 15 (lưu vào figures/):
python member1_charts_week15.py
```

Lưu ý: các số về tốc độ (throughput, latency, cache speedup) sẽ KHÁC nhau
tùy máy. Các số do dữ liệu quyết định (tỷ lệ URL, độ dài, số mẫu) thì giống nhau.

---

## 5. Cấu trúc module data/

```
data/
├── preprocessor.py   # LÕI: làm sạch 1 email -> Record (HTML strip, URL, SPF/DKIM/DMARC)
├── datasets.py       # nạp nhiều email, chia train/test
├── cache.py          # NEW Week 15: cache xuống đĩa, tăng tốc chạy lại
├── __init__.py       # interface public (import từ đây)
└── samples/          # dữ liệu JSON đã xử lý
```

Có gì thắc mắc về phần data, nhắn Lan nhé.
