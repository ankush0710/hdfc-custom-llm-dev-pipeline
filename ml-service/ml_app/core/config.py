"""
ml-service/app/core/config.py

Configuration for the ML Service worker.
Loads environment variables for Neon PostgreSQL, Hugging Face, and service security.
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

_logger = logging.getLogger(__name__)

# Repository roots
ML_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ML_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Load .env if present in ml-service, fallback to backend/.env for smooth local development
if (ML_DIR / ".env").exists():
    load_dotenv(ML_DIR / ".env")
elif (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env")

# Database & Storage
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    _logger.warning("DATABASE_URL is not set in ML Service. Direct Neon DB telemetry updates will be skipped.")

HF_TOKEN = os.getenv("HF_TOKEN")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "ankush0710/hdfc-llm-datasets")
HF_MODEL_REPO = os.getenv("HF_MODEL_REPO", "ankush0710/hdfc-llm-models")
HF_UPLOAD_TIMEOUT_SECONDS = int(os.getenv("HF_UPLOAD_TIMEOUT_SECONDS", "900"))
HF_LOCAL_TEMP_DIR = Path(os.getenv("HF_LOCAL_TEMP_DIR", BACKEND_DIR / "storage" / "temp_hf")).resolve()
HF_LOCAL_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Service Authentication & Networking
ML_SERVICE_API_KEY = os.getenv("ML_SERVICE_API_KEY", "hdfc-internal-ml-service-key")
PORT = int(os.getenv("PORT", os.getenv("ML_SERVICE_PORT", "8001")))
HOST = os.getenv("HOST", "0.0.0.0")

# AI Inference Settings
AI_DEVICE = os.getenv("AI_DEVICE", "auto")
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "qwen3_0_6b")
AI_MAX_NEW_TOKENS = int(os.getenv("AI_MAX_NEW_TOKENS", "256"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))
AI_TOP_P = float(os.getenv("AI_TOP_P", "0.9"))
AI_DO_SAMPLE = os.getenv("AI_DO_SAMPLE", "false").lower() == "true"
