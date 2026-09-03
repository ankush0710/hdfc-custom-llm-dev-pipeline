"""
ml-service/run_service.py

Alias wrapper for run_server.py so both `python run_service.py` and `python run_server.py` work.
"""
from pathlib import Path
import runpy

if __name__ == "__main__":
    server_script = Path(__file__).resolve().parent / "run_server.py"
    runpy.run_path(str(server_script), run_name="__main__")
