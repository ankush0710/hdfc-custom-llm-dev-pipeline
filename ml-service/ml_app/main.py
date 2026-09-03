"""
ml-service/app/main.py

FastAPI entrypoint for the dedicated HDFC Custom LLM ML Service.
Hosts heavy ML workloads: LoRA Training, Model Evaluation, and Real-time Inference.
"""
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_app_dir = Path(__file__).resolve().parent
_ml_dir = _app_dir.parent
_repo_root = _ml_dir.parent

for p in [str(_ml_dir), str(_repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from .core.config import HOST, PORT
from .routes.inference_routes import router as inference_router
from .routes.training_routes import router as training_router
from .routes.evaluation_routes import router as evaluation_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ml_service")

app = FastAPI(
    title="HDFC Custom LLM - ML Service Worker",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Include ML Worker Routers
app.include_router(inference_router)
app.include_router(training_router)
app.include_router(evaluation_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Unauthenticated health probe for monitoring and service discovery."""
    return {
        "status": "healthy",
        "service": "hdfc-custom-llm-ml-worker",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ML Service on %s:%d ...", HOST, PORT)
    uvicorn.run(
        "ml_app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
    )
