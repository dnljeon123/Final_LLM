"""
Convert Kaggle Phishing Email Dataset CSVs into the project's JSON format.

This script reads multiple CSV files, samples a balanced number of
phishing/legitimate emails, and writes a unified JSON file that
data.datasets can load.

Usage:
    python convert_kaggle_dataset.py
"""
import csv
import json
import random
import sys
from pathlib import Path

# ----- CONFIG -----
KAGGLE_DIR = Path("kaggle_fishing")  # folder containing the CSV files
OUTPUT_FILE = Path("data/samples/kaggle_dataset.json")
SAMPLES_PER_CLASS = 100  # how many phishing + legit to sample (200 total)
RANDOM_SEED = 42

# CSV files to read. Each entry: (filename, label_override OR column_name)
# If label_override is an int (0 or 1), all rows get that label.
# If it's a string, read the label from that column.
CSV_FILES = [
    # Phishing-only files — force label=1
    ("Nazario.csv", 1),
    ("Nigerian_Fraud.csv", 1),
    ("phishing_email.csv", 1),
    # Legit baseline — Enron is mostly legitimate business email
    ("Enron.csv", 0),
    # Mixed datasets — use their own label column (will try common names)
    # ("CEAS_08.csv", "label"),
    # ("SpamAssasin.csv", "label"),
]

# Increase csv field size limit (some emails have huge bodies)
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def find_column(headers, candidates):
    """Return the first header that matches any candidate (case-insensitive)."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for cand in candidates:
        if cand.lower() in lower_headers:
            return lower_headers[cand.lower()]
    return None


def read_csv_rows(path: Path, label_or_col):
    """Read a CSV and yield dicts: {subject, body, sender, label}."""
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        # Sniff dialect
        try:
            sample = f.read(8192)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []

        body_col = find_column(headers, ["body", "text", "email", "message", "content"])
        subject_col = find_column(headers, ["subject", "title"])
        sender_col = find_column(headers, ["sender", "from", "from_address"])
        label_col = label_or_col if isinstance(label_or_col, str) else None
        if label_col:
            label_col = find_column(headers, [label_col, "label", "class", "is_phishing"])

        if not body_col:
            print(f"  [WARN] {path.name}: no body-like column found in {headers}")
            return

        for row in reader:
            body = (row.get(body_col, "") or "").strip()
            if not body or len(body) < 30:
                continue  # skip empty/tiny rows
            subject = (row.get(subject_col, "") or "").strip() if subject_col else ""
            sender = (row.get(sender_col, "") or "").strip() if sender_col else ""

            if isinstance(label_or_col, int):
                label = label_or_col
            else:
                raw_label = (row.get(label_col, "") or "").strip().lower()
                if raw_label in ("1", "phishing", "spam", "phish", "yes", "true"):
                    label = 1
                elif raw_label in ("0", "ham", "legitimate", "legit", "no", "false"):
                    label = 0
                else:
                    continue  # unknown label, skip

            yield {
                "subject": subject,
                "body": body,
                "sender": sender,
                "label": label,
            }


def main():
    if not KAGGLE_DIR.exists():
        print(f"ERROR: folder {KAGGLE_DIR} not found. Are you in the poc/ directory?")
        return 1

    print(f"Reading CSV files from {KAGGLE_DIR}/ ...\n")

    phishing_rows = []
    legit_rows = []

    for filename, label_spec in CSV_FILES:
        path = KAGGLE_DIR / filename
        if not path.exists():
            print(f"  [SKIP] {filename} not found")
            continue
        count_before_p, count_before_l = len(phishing_rows), len(legit_rows)
        for row in read_csv_rows(path, label_spec):
            if row["label"] == 1:
                phishing_rows.append(row)
            else:
                legit_rows.append(row)
        print(f"  {filename:25s} +{len(phishing_rows) - count_before_p} phishing, "
              f"+{len(legit_rows) - count_before_l} legit")

    print(f"\nTotal collected: {len(phishing_rows)} phishing, {len(legit_rows)} legit")

    if not phishing_rows or not legit_rows:
        print("ERROR: missing one class. Check the column names with `Get-Content file.csv -Head 2`")
        return 1

    # Stratified sampling — balanced classes
    rng = random.Random(RANDOM_SEED)
    n = min(SAMPLES_PER_CLASS, len(phishing_rows), len(legit_rows))
    sampled_phish = rng.sample(phishing_rows, n)
    sampled_legit = rng.sample(legit_rows, n)
    all_samples = sampled_phish + sampled_legit
    rng.shuffle(all_samples)

    # Convert to the project's expected JSON format
    out = []
    for i, row in enumerate(all_samples):
        # Reconstruct as plain text (mimicking the email format)
        parts = []
        if row["sender"]:
            parts.append(f"From: {row['sender']}")
        if row["subject"]:
            parts.append(f"Subject: {row['subject']}")
        parts.append("")
        parts.append(row["body"])
        text = "\n".join(parts)

        out.append({
            "name": f"kaggle_{'phish' if row['label'] == 1 else 'legit'}_{i:04d}",
            "label": row["label"],
            "text": text,
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Wrote {len(out)} samples to {OUTPUT_FILE}")
    print(f"     - Phishing: {sum(1 for x in out if x['label'] == 1)}")
    print(f"     - Legit:    {sum(1 for x in out if x['label'] == 0)}")
    print(f"\nNext step: run your experiments or evaluation harness on this dataset.")
    print(f"  python -m eval.harness --strategy cot --test-set {OUTPUT_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
