import re
from pathlib import Path

import pandas as pd


RAW_DIR = Path(".")

CLEAN_DIR = Path("cleaned_excel")


FILES = [
    "accounts.xlsx",
    "BANKING77_Real_Banking_Dataset.xlsx",
    "banking_knowledge_base_1000.xlsx",
    "bank_faq.xlsx",
    "credit_cards.xlsx",
    "customers.xlsx",
    "customer_queries.xlsx",
    "HDFC_Custom_LLM_7000rows_Dataset_Suite-v2.xlsx",
    "HDFC_Faq.xlsx",
    "loans.xlsx",
    "transactions.xlsx",
]


BAD_ENCODING = (
    "â‚¹",
    "â€“",
    "â€”",
    "â€™",
    "â€œ",
    "â€",
)

PII_PATTERNS = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "phone": re.compile(
        r"\b(?:\+91[- ]?)?[6-9]\d{9}\b"
    ),
}


def check_text(df):
    encoding_hits = 0
    pii_hits = {name: 0 for name in PII_PATTERNS}

    for column in df.columns:
        if not pd.api.types.is_string_dtype(df[column]):
            continue

        series = df[column].fillna("").astype(str)

        for value in series:
            for bad in BAD_ENCODING:
                if bad in value:
                    encoding_hits += 1

            for name, pattern in PII_PATTERNS.items():
                if pattern.search(value):
                    pii_hits[name] += 1

    return encoding_hits, pii_hits


def audit_pair(raw_path, clean_path):
    print("\n" + "=" * 80)
    print(f"RAW:     {raw_path.name}")
    print(f"CLEANED: {clean_path.name}")
    print("=" * 80)

    if not raw_path.exists():
        print("RAW FILE: MISSING")
        return False

    if not clean_path.exists():
        print("CLEANED FILE: MISSING")
        return False

    raw = pd.read_excel(raw_path)
    clean = pd.read_excel(clean_path)

    print(f"Raw rows:              {len(raw):,}")
    print(f"Cleaned rows:          {len(clean):,}")

    print(f"Raw columns:            {len(raw.columns)}")
    print(f"Cleaned columns:        {len(clean.columns)}")

    same_columns = list(raw.columns) == list(clean.columns)

    print(f"Column structure same:  {same_columns}")

    if not same_columns:
        print("\nRAW COLUMNS:")
        print(list(raw.columns))

        print("\nCLEANED COLUMNS:")
        print(list(clean.columns))

    raw_empty = raw.isna().all(axis=1).sum()
    clean_empty = clean.isna().all(axis=1).sum()

    print(f"Completely empty raw rows:     {raw_empty:,}")
    print(f"Completely empty clean rows:   {clean_empty:,}")

    raw_encoding, raw_pii = check_text(raw)
    clean_encoding, clean_pii = check_text(clean)

    print(f"\nRaw encoding hits:             {raw_encoding:,}")
    print(f"Cleaned encoding hits:         {clean_encoding:,}")

    print(f"\nRaw possible PII:")
    print(f"  email: {raw_pii['email']:,}")
    print(f"  phone: {raw_pii['phone']:,}")

    print(f"\nCleaned possible PII:")
    print(f"  email: {clean_pii['email']:,}")
    print(f"  phone: {clean_pii['phone']:,}")

    raw_duplicates = raw.duplicated().sum()
    clean_duplicates = clean.duplicated().sum()

    print(f"\nDuplicate raw rows:            {raw_duplicates:,}")
    print(f"Duplicate cleaned rows:        {clean_duplicates:,}")

    return True


def main():
    passed_files = 0

    for raw_name in FILES:
        raw_path = RAW_DIR / raw_name

        cleaned_name = Path(raw_name).stem + "_cleaned.xlsx"
        clean_path = CLEAN_DIR / cleaned_name

        if audit_pair(raw_path, clean_path):
            passed_files += 1

    print("\n" + "=" * 80)
    print("FINAL EXCEL AUDIT")
    print("=" * 80)
    print(f"Files successfully audited: {passed_files}/{len(FILES)}")

    if passed_files == len(FILES):
        print("All 11 cleaned Excel files are present.")
    else:
        print("WARNING: One or more cleaned Excel files are missing.")


if __name__ == "__main__":
    main()