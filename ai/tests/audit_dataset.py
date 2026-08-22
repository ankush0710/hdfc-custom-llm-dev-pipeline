import json
import re
from collections import Counter
from pathlib import Path


FILES = {
    "train": Path("hdfc_llm_train.jsonl"),
    "val": Path("hdfc_llm_val.jsonl"),
    "test": Path("hdfc_llm_test.jsonl"),
}

APPROVED_TASK_TYPES = {
    "intent_classification",
    "sft_grounded_generation",
    "customer_faq_qa",
    "domain_concept_qa",
}

REQUIRED_FIELDS = {
    "record_id",
    "source",
    "task_type",
    "domain",
    "instruction",
    "context",
    "response",
    "messages",
    "hash",
}

BAD_ENCODING = (
    "â‚¹",
    "â€“",
    "â€”",
    "â€™",
    "â€œ",
    "â€",
)

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+91[- ]?)?[6-9]\d{9}\b"),
}


def audit_file(path: Path):
    print(f"\n{'=' * 70}")
    print(f"AUDITING: {path}")
    print(f"{'=' * 70}")

    if not path.exists():
        print("ERROR: File not found")
        return None

    total = 0
    invalid_json = 0
    missing_fields = 0
    empty_fields = 0
    bad_task_types = Counter()
    encoding_hits = Counter()
    pii_hits = Counter()
    hashes = Counter()
    records = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.rstrip("\n")

            if not line.strip():
                continue

            total += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                continue

            records.append(record)

            missing = REQUIRED_FIELDS - record.keys()
            if missing:
                missing_fields += 1

            for field in ("instruction", "context", "response"):
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    empty_fields += 1

            task_type = record.get("task_type")

            if task_type not in APPROVED_TASK_TYPES:
                bad_task_types[task_type] += 1

            for bad_text in BAD_ENCODING:
                if bad_text in line:
                    encoding_hits[bad_text] += 1

            for name, pattern in PII_PATTERNS.items():
                if pattern.search(line):
                    pii_hits[name] += 1

            record_hash = record.get("hash")
            if record_hash:
                hashes[record_hash] += 1

    duplicate_records = sum(
        count - 1 for count in hashes.values() if count > 1
    )

    print(f"Records:              {total}")
    print(f"Invalid JSON lines:   {invalid_json}")
    print(f"Missing fields:       {missing_fields}")
    print(f"Empty required text:  {empty_fields}")
    print(f"Duplicate hashes:     {duplicate_records}")

    print("\nTask distribution:")
    task_counts = Counter(r.get("task_type") for r in records)
    for task, count in task_counts.most_common():
        print(f"  {task}: {count}")

    print("\nUnexpected task types:")
    print(f"  {dict(bad_task_types) if bad_task_types else 'NONE'}")

    print("\nEncoding corruption:")
    print(f"  {dict(encoding_hits) if encoding_hits else 'NONE'}")

    print("\nPossible PII:")
    print(f"  {dict(pii_hits) if pii_hits else 'NONE'}")

    return records


def main():
    all_records = {}

    for split, path in FILES.items():
        all_records[split] = audit_file(path)

    print(f"\n{'=' * 70}")
    print("CROSS-SPLIT DUPLICATE CHECK")
    print(f"{'=' * 70}")

    if any(records is None for records in all_records.values()):
        print("Skipped because one or more files were missing.")
        return

    split_hashes = {
        split: {
            record.get("hash")
            for record in records
            if record.get("hash")
        }
        for split, records in all_records.items()
    }

    train_val = split_hashes["train"] & split_hashes["val"]
    train_test = split_hashes["train"] & split_hashes["test"]
    val_test = split_hashes["val"] & split_hashes["test"]

    print(f"Train ∩ Validation: {len(train_val)}")
    print(f"Train ∩ Test:       {len(train_test)}")
    print(f"Validation ∩ Test:  {len(val_test)}")

    print(f"\n{'=' * 70}")
    print("FINAL DATASET QUALITY GATE")
    print(f"{'=' * 70}")

    passed = True

    for split, records in all_records.items():
        if records is None:
            passed = False
            continue

        for record in records:
            if record.get("task_type") not in APPROVED_TASK_TYPES:
                passed = False

            for field in REQUIRED_FIELDS:
                if field not in record:
                    passed = False

            for field in ("instruction", "context", "response"):
                if not isinstance(record.get(field), str):
                    passed = False
                elif not record[field].strip():
                    passed = False

    if train_val or train_test or val_test:
        passed = False

    if passed:
        print("STATUS: PASSED")
        print("Dataset is ready for the next training stage.")
    else:
        print("STATUS: FAILED")
        print("Do NOT start training yet.")


if __name__ == "__main__":
    main()