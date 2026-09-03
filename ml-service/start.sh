#!/usr/bin/env bash
# Start script for HDFC ML Service worker
set -e

PORT=${PORT:-8001}
HOST=${HOST:-0.0.0.0}

echo "Starting HDFC ML Service on $HOST:$PORT..."
exec uvicorn ml_app.main:app --host "$HOST" --port "$PORT" --workers 1
