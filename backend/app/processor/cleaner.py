# ================================================================================= #
# function to find and remove wrong, empty values from the dataset
# ================================================================================= #
import pandas as pd

def clean_file(df: pd.DataFrame):

    new_df = df.copy()

    # Remove the empty rows 
    new_df.dropna(inplace="True", how="all")

    # Remove completely empty rows 
    df.dropna(inplace="True", axis=1, how="all")

    # strip whitespace from string column 
    string_columns = df.select_dtypes(
        include = ["object", "string"]
    ).columns

    for columns in string_columns:
        df[columns] = df[columns].select_dtypes(
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

    df = df.replace(
        missing_value,
        pd.NA
    )

    return df
