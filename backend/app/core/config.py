import logging
import os
from pathlib import Path

from dotenv import load_dotenv

_logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set ...")

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    _logger.warning(
        "HF_TOKEN env var is not set. "
        "HuggingFace Hub model upload and dataset download will fail at runtime."
    )

HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "ankush0710/hdfc-llm-datasets")
HF_MODEL_REPO = os.getenv("HF_MODEL_REPO", "ankush0710/hdfc-llm-models")
HF_UPLOAD_TIMEOUT_SECONDS = int(os.getenv("HF_UPLOAD_TIMEOUT_SECONDS", "900"))

HF_LOCAL_TEMP_DIR = Path(os.getenv("HF_LOCAL_TEMP_DIR", BACKEND_DIR / "storage" / "temp_hf")).resolve()
HF_LOCAL_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ML Service Communication Configuration
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
ML_SERVICE_API_KEY = os.getenv("ML_SERVICE_API_KEY", "hdfc-internal-ml-service-key")
ML_SERVICE_TIMEOUT_SECONDS = float(os.getenv("ML_SERVICE_TIMEOUT_SECONDS", "120.0"))
