"""
backend/run_server.py

Convenience runner for the backend API so `python run_server.py` works in both backend/ and ml-service/.
"""
from pathlib import Path
import runpy

if __name__ == "__main__":
    prod_script = Path(__file__).resolve().parent / "start_prod.py"
    runpy.run_path(str(prod_script), run_name="__main__")
