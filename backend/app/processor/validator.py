# ================================================================================== #
# function for validate the dataset -> supported extension, split text, file_size
# ================================================================================== #
import os
import pandas as pd

supported_extension = ['.csv', '.xlsx', '.jsonl', '.json']

def resolve_file_path(file_path: str) -> str:
    if os.path.exists(file_path):
        return file_path
    backend_rel = os.path.join("backend", file_path)
    if os.path.exists(backend_rel):
        return backend_rel
    if file_path.startswith("backend/") or file_path.startswith("backend\\"):
        stripped = file_path[len("backend/"):].lstrip("/\\")
        if os.path.exists(stripped):
            return stripped
    return file_path

def validate_file(file_path: str):
    resolved = resolve_file_path(file_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Dataset file does not exist: {file_path}")

    extension = os.path.splitext(resolved)[-1].strip().lower()

    if extension not in supported_extension:
        raise ValueError(
            f"Unsupported File Format: {extension}"
        )

    return True

def load_file(file_path: str):
    resolved = resolve_file_path(file_path)
    validate_file(resolved)

    extension = os.path.splitext(resolved)[-1].strip().lower()

    if extension == ".csv":
        df = pd.read_csv(resolved)

    elif extension == ".xlsx":
        df = pd.read_excel(resolved)

    elif extension in [".json", ".jsonl"]:
        df = pd.read_json(resolved, lines=(extension == ".jsonl"))
    else:
        raise ValueError(f"File format {extension} cannot be loaded into DataFrame.")


    if df.empty:
        raise ValueError("Dataset is empty.")

    if len(df.columns) == 0:
        raise ValueError("Dataset has no columns.")

    return df






    

    
