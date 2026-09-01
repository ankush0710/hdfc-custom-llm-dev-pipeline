import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set ...")

HF_TOKEN = os.getenv("HF_TOKEN")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "ankush0710/hdfc-llm-datasets")
HF_MODEL_REPO = os.getenv("HF_MODEL_REPO", "ankush0710/hdfc-llm-models")

HF_LOCAL_TEMP_DIR = Path(os.getenv("HF_LOCAL_TEMP_DIR", BACKEND_DIR / "storage" / "temp_hf")).resolve()
HF_LOCAL_TEMP_DIR.mkdir(parents=True, exist_ok=True)

