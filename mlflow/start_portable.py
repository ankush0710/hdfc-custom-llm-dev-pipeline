"""Start the bundled MLflow evidence store portably from any extraction directory.

This package is an evidence snapshot rather than a live production MLflow deployment.
MLflow stores local artifact URIs as filesystem locations, so the bundled SQLite DB may
contain an absolute path from the machine that created the snapshot. This launcher
rebinds local run artifact URIs to the package's *current* extraction directory before
starting a single-worker local MLflow server.
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PACKAGE_ROOT / "mlflow.db"
MLRUNS_ROOT = PACKAGE_ROOT / "mlruns"


def _portable_artifact_uri(run_uuid: str, experiment_id: str) -> str:
    artifact_dir = MLRUNS_ROOT / str(experiment_id) / run_uuid / "artifacts"
    if not artifact_dir.is_dir():
        raise FileNotFoundError(
            f"Expected artifact directory is missing for run {run_uuid}: {artifact_dir}"
        )
    return artifact_dir.as_uri()


def rebind_local_artifacts() -> tuple[int, int]:
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"MLflow database not found: {DB_PATH}")
    if not MLRUNS_ROOT.is_dir():
        raise FileNotFoundError(f"MLflow artifact store not found: {MLRUNS_ROOT}")

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT run_uuid, experiment_id, artifact_uri, lifecycle_stage FROM runs"
        ).fetchall()
        updated = 0
        skipped = 0
        for run_uuid, experiment_id, artifact_uri, lifecycle_stage in rows:
            scheme = urlparse(artifact_uri or "").scheme
            # Only rewrite local file-backed artifacts bundled in this package.
            if scheme not in ("", "file"):
                continue

            artifact_dir = MLRUNS_ROOT / str(experiment_id) / run_uuid / "artifacts"
            # Historical/deleted MLflow runs may be retained in the SQLite evidence DB
            # without their artifact payloads. They do not block a portable snapshot.
            if not artifact_dir.is_dir():
                skipped += 1
                print(
                    f"Skipping run {run_uuid} (lifecycle={lifecycle_stage or 'unknown'}): "
                    f"bundled artifact directory not present: {artifact_dir}"
                )
                continue

            new_uri = artifact_dir.as_uri()
            if artifact_uri != new_uri:
                conn.execute(
                    "UPDATE runs SET artifact_uri=? WHERE run_uuid=?",
                    (new_uri, run_uuid),
                )
                updated += 1
        conn.commit()
        return updated, skipped
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebind bundled MLflow artifacts to this extraction directory and start MLflow UI."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    updated, skipped = rebind_local_artifacts()
    print(f"Package root: {PACKAGE_ROOT}")
    print(f"MLflow database: {DB_PATH}")
    print(f"Artifact store: {MLRUNS_ROOT}")
    print(f"Rebound local artifact URIs: {updated}")
    print(f"Runs without bundled artifacts skipped: {skipped}")
    print(f"Starting MLflow on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")

    cmd = [
        sys.executable,
        "-m",
        "mlflow",
        "server",
        "--backend-store-uri",
        f"sqlite:///{DB_PATH.as_posix()}",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--workers",
        "1",
    ]
    return subprocess.call(cmd, cwd=PACKAGE_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
