import re
import pandas as pd

ENCODING_REPLACEMENTS = {
    'â€“': '—',
    'â€”': '—',
    'â€™': "'",
    'â€œ': '"',
    'â€': '"',
    '\u00e2\u20ac\u201c': '—',
    '\u00e2\u20ac\u2122': "'",
    'â‚¹': '₹',
}

def fix_encoding(text: str) -> str:
    if not isinstance(text, str):
        return text
    for bad, good in ENCODING_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return re.sub(r'\s+', ' ', text).strip()

def clean_file(df: pd.DataFrame) -> pd.DataFrame:
    new_df = df.copy()

    # Remove completely empty rows
    new_df.dropna(inplace=True, how="all")

    # Remove completely empty columns
    new_df.dropna(inplace=True, axis=1, how="all")

    # Fix encoding and strip whitespace from string columns
    for col in new_df.columns:
        new_df[col] = new_df[col].apply(
            lambda value: fix_encoding(value) if isinstance(value, str) else value
        )

    # Normalize common missing values
    missing_value = [
        "",
        "NA",
        "N/A",
        "null",
        "Null",
        "none",
        "None"
    ]

    new_df = new_df.replace(
        missing_value,
        pd.NA
    )

    return new_df
