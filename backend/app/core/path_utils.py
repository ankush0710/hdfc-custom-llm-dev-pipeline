"""
backend/app/core/path_utils.py

Backend re-export of central artifact resolution and validation utilities.
"""
from ai.utils.path_utils import (
    PROJECT_ROOT,
    BACKEND_ROOT,
    AI_ROOT,
    ARTIFACT_SEARCH_DIRS,
    resolve_artifact_path,
    validate_artifact_directory,
)

__all__ = [
    "PROJECT_ROOT",
    "BACKEND_ROOT",
    "AI_ROOT",
    "ARTIFACT_SEARCH_DIRS",
    "resolve_artifact_path",
    "validate_artifact_directory",
]
