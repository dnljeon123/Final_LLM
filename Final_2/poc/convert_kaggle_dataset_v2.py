"""
Convert Kaggle Phishing Email Dataset CSVs into the project's JSON format.

Week 15 changes vs v1:
  - Add 'text_combined' column name to body detection (enables phishing_email.csv)
  - Scale from 100/100 to 500/500 samples (configurable)
  - Add a small synthetic GitHub-style legitimate baseline with realistic URLs
    to address the "Enron has no URLs" finding from Week 14

Usage:
    python convert_kaggle_dataset_v2.py
"""
import csv
import json
import random
import sys
from pathlib import Path

KAGGLE_DIR = Path("kaggle_fishing")
OUTPUT_FILE = Path("data/samples/kaggle_dataset_v2.json")
SAMPLES_PER_CLASS = 500  # SCALED UP from 100 to 500
RANDOM_SEED = 42

CSV_FILES = [
    ("Nazario.csv", 1),
    ("Nigerian_Fraud.csv", 1),
    ("phishing_email.csv", 1),  # Now enabled (text_combined column)
    ("Enron.csv", 0),
]

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def find_column(headers, candidates):
    lower_headers = {h.lower().strip(): h for h in headers}
    for cand in candidates:
        if cand.lower() in lower_headers:
            return lower_headers[cand.lower()]
    return None


def read_csv_rows(path: Path, label_or_col):
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        try:
            sample = f.read(8192)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []

        # KEY CHANGE: added 'text_combined' to candidate list
        body_col = find_column(headers, ["body", "text", "email", "message",
                                          "content", "text_combined"])
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
                continue
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
                    continue

            yield {"subject": subject, "body": body, "sender": sender, "label": label}


def synthetic_legit_with_urls():
    """
    Generate synthetic legitimate emails WITH realistic URLs.
    This addresses the Week 14 finding that Enron has 0 URLs (artifact of dataset).
    Mimics common legitimate email patterns: GitHub, Stripe, Slack notifications.
    """
    templates = [
        ("notifications@github.com",
         "[user/repo] Pull request opened: {topic} (#{n})",
         "A new pull request was opened by @contributor-{n}.\n\n"
         "Review the changes at: https://github.com/user/repo/pull/{n}\n\n"
         "--\nManage notifications: https://github.com/settings/notifications"),

        ("noreply@stripe.com",
         "Your invoice for {topic} is ready",
         "Hi,\n\nYour invoice for {topic} is now available.\n\n"
         "View invoice: https://invoice.stripe.com/i/acct_xxx/test_{n}\n"
         "Download PDF: https://files.stripe.com/invoice_{n}.pdf\n\n"
         "Thanks for using Stripe.\nThe Stripe Team"),

        ("no-reply@slack.com",
         "Daily summary for #{topic}",
         "Here's what you missed in #{topic} today:\n\n"
         "- 5 new messages from @teammate\n"
         "- 2 threads need your input\n\n"
         "View in Slack: https://workspace.slack.com/archives/C{n}\n"
         "Unsubscribe: https://slack.com/account/notifications"),

        ("notifications@linkedin.com",
         "{topic} - new activity on your post",
         "Your recent post about {topic} has new activity:\n\n"
         "- 12 reactions\n- 3 comments\n\n"
         "See full activity: https://www.linkedin.com/feed/update/urn:li:activity:{n}\n"
         "Manage emails: https://www.linkedin.com/settings"),

        ("team@notion.so",
         "Weekly digest from your workspace",
         "This week in your workspace:\n\n"
         "- 4 new pages created\n- 12 edits to shared documents\n\n"
         "Open workspace: https://www.notion.so/workspace-{n}\n"
         "Email preferences: https://www.notion.so/preferences"),

        ("hello@figma.com",
         "Your design '{topic}' was viewed {n} times",
         "Hi there,\n\nYour design '{topic}' was viewed by {n} people this week.\n\n"
         "View analytics: https://www.figma.com/file/abc{n}/analytics\n"
         "Open file: https://www.figma.com/file/abc{n}\n\n"
         "Cheers,\nThe Figma Team"),
    ]

    topics = ["Q4 planning", "API redesign", "frontend bug fix", "database migration",
              "user research", "release notes", "security audit", "performance review",
              "design system", "mobile app", "documentation", "feature rollout"]

    rng = random.Random(RANDOM_SEED)
    out = []
    for i in range(200):  # generate 200 synthetic legitimate emails
        sender, subject_tpl, body_tpl = rng.choice(templates)
        topic = rng.choice(topics)
        n = rng.randint(100, 9999)
        subject = subject_tpl.format(topic=topic, n=n)
        body = body_tpl.format(topic=topic, n=n)
        out.append({
            "subject": subject,
            "body": body,
            "sender": sender,
            "label": 0,
        })
    return out


def main():
    if not KAGGLE_DIR.exists():
        print(f"ERROR: folder {KAGGLE_DIR} not found.")
        return 1

    print(f"Reading CSV files from {KAGGLE_DIR}/ ...\n")

    phishing_rows = []
    legit_rows = []

    for filename, label_spec in CSV_FILES:
        path = KAGGLE_DIR / filename
        if not path.exists():
            print(f"  [SKIP] {filename} not found")
            continue
        cb_p, cb_l = len(phishing_rows), len(legit_rows)
        for row in read_csv_rows(path, label_spec):
            if row["label"] == 1:
                phishing_rows.append(row)
            else:
                legit_rows.append(row)
        print(f"  {filename:25s} +{len(phishing_rows) - cb_p:6d} phishing, "
              f"+{len(legit_rows) - cb_l:6d} legit")

    # Add synthetic GitHub/Stripe/etc emails to address Enron URL=0 issue
    synthetic = synthetic_legit_with_urls()
    legit_rows.extend(synthetic)
    print(f"  {'synthetic_legit (NEW)':25s} +{0:6d} phishing, +{len(synthetic):6d} legit")

    print(f"\nTotal collected: {len(phishing_rows)} phishing, {len(legit_rows)} legit")

    if not phishing_rows or not legit_rows:
        print("ERROR: missing one class.")
        return 1

    rng = random.Random(RANDOM_SEED)
    n = min(SAMPLES_PER_CLASS, len(phishing_rows), len(legit_rows))

    # For legit: ensure ~80% Enron + 20% synthetic (to maintain realism but fix URL issue)
    n_synthetic = min(n // 5, len(synthetic))
    n_enron = n - n_synthetic
    enron_only = [r for r in legit_rows if r not in synthetic]
    sampled_legit = rng.sample(enron_only, n_enron) + rng.sample(synthetic, n_synthetic)

    sampled_phish = rng.sample(phishing_rows, n)

    all_samples = sampled_phish + sampled_legit
    rng.shuffle(all_samples)

    out = []
    for i, row in enumerate(all_samples):
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
    print(f"       (of which ~{n_synthetic} are synthetic GitHub/Stripe-style with URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
