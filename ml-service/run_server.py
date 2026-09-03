"""
ml-service/run_server.py

Runner script for starting the ML Service worker locally or on a server.
Automatically re-executes using the project's virtualenv interpreter if called with global python.
"""
import os
import sys
from pathlib import Path

_service_dir = Path(__file__).resolve().parent
_repo_root = _service_dir.parent

# 1. Auto-detect project virtual environment if run with global python
_venv_candidates = [
    _repo_root / "backend" / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
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
        res = subprocess.run([str(_venv_py)] + sys.argv, cwd=str(_service_dir), env=_env)
        sys.exit(res.returncode)

# 2. Add service directory and repo root to sys.path
for p in [str(_service_dir), str(_repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import uvicorn
from ml_app.core.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting ML Service on {HOST}:{PORT} ...")
    uvicorn.run(
        "ml_app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
    )
