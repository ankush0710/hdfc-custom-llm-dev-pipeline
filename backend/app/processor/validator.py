# ================================================================================== #
# function for validate the dataset -> supported extension, split text, file_size
# ================================================================================== #
import os
import pandas as pd

supported_extension = ['.csv', '.pdf', 'xlsx', 'jsonl']

def validate_file(file_path: str):

    if not os.path.exists(file_path):
        raise FileNotFoundError("Dataset file not exists")


    extension = os.path.splitext(file_path)[-1].strip().lower()

    if extension not in supported_extension:
        raise ValueError(
            f"Unsupportes File Format: {extension}"
        )

    return True

def load_file(file_path: str):

    validate_file(file_path)

    extension = os.path.splitext(file_path)[-1].strip().lower()

    if extension == ".csv":
        df = pd.read_csv(file_path)

    elif extension == ".pdf":
        df = pd.read_pdf(file_path)

    elif extension == ".xlsx":
        df = pd.read_excel(file_path)

    elif extension == ".json":
        df = pd.read_json(file_path)
    else:
        raise ValueError("Unsupported File Format.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    if len(df.columns) == 0:
        raise ValueError("Dataset has no columns.")

    return df






    

    
