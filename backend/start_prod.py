#!/usr/bin/env python3
"""
start_prod.py — Production startup script for the HDFC Custom LLM backend.
Automatically re-executes using the project's virtualenv interpreter if called with global python.
"""
import os
import sys
from pathlib import Path

# 1. Auto-detect project virtual environment if run with global python
_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent

_venv_candidates = [
    _backend_dir / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
    _repo_root / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
]

_current_exe = Path(sys.executable).resolve()
_resolved_venvs = [c.resolve() for c in _venv_candidates if c.is_file()]

# If we are already running inside one of the recognized project venvs, do NOT re-launch!
if _current_exe not in _resolved_venvs and not os.getenv("__RELAUNCHED_VENV"):
    for _venv_py in _resolved_venvs:
        import subprocess
        _env = os.environ.copy()
        _env["__RELAUNCHED_VENV"] = "1"
        res = subprocess.run([str(_venv_py)] + sys.argv, cwd=str(_backend_dir), env=_env)
        sys.exit(res.returncode)

# 2. Add backend directory and repo root to sys.path
for p in [str(_backend_dir), str(_repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import uvicorn

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


if __name__ == "__main__":
    print(f"Starting HDFC LLM API on {HOST}:{PORT} [ENVIRONMENT={os.getenv('ENVIRONMENT', 'development')}]")
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=os.getenv("RELOAD", "true").lower() == "true",
        workers=1,
        log_level=LOG_LEVEL,
        access_log=True,
        loop="asyncio",
    )
