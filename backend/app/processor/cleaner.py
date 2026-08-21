# ================================================================================= #
# function to find and remove wrong, empty values from the dataset
# ================================================================================= #
import pandas as pd

def clean_file(df: pd.DataFrame):

    new_df = df.copy()

    # Remove empty rows 
    new_df.dropna(inplace=True, how="all")

    # Remove completely empty columns 
    new_df.dropna(inplace=True, axis=1, how="all")

    # strip whitespace from string column 
    string_columns = new_df.select_dtypes(
        include = ["object", "string"]
    ).columns

    for col in string_columns:
        new_df[col] = new_df[col].apply(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
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
