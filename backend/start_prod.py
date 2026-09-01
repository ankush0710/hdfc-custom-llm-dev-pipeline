#!/usr/bin/env python3
"""
start_prod.py — Production startup script for the HDFC Custom LLM backend.

Key differences from the dev command (uvicorn app.main:app --reload):
  - --reload is REMOVED: hot-reload evicts the in-memory model cache, causing
    60-300s cold-start latencies on every file change.
  - --workers 1: a single Uvicorn worker ensures the ai.inference.service._active
    model cache is shared across all requests in the same process. Multiple
    workers would each load their own copy of the model, wasting VRAM.
  - --log-level warning: suppresses verbose INFO logs in production while
    retaining WARNING / ERROR output.
  - ENVIRONMENT=production must be set in the environment (or .env.production)
    to disable /docs, /redoc, and /openapi.json.

Usage (development):
    python start_prod.py

Usage (production / Docker):
    ENVIRONMENT=production ALLOW_ORIGIN=https://your-frontend.com python start_prod.py

Or with gunicorn (recommended for Linux production):
    gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 1 --bind 0.0.0.0:8000
"""
import os
import sys

import uvicorn

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "warning")


if __name__ == "__main__":
    print(f"Starting HDFC LLM API on {HOST}:{PORT} [ENVIRONMENT={os.getenv('ENVIRONMENT', 'development')}]")
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,           # NEVER enable reload in production — kills model cache
        workers=1,              # Single worker: preserves the module-level model cache
        log_level=LOG_LEVEL,
        access_log=True,
        loop="asyncio",
    )
