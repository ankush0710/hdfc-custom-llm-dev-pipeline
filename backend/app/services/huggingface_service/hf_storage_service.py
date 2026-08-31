import hashlib
import io
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError

from app.core.config import (
    HF_DATASET_REPO,
    HF_LOCAL_TEMP_DIR,
    HF_MODEL_REPO,
    HF_TOKEN,
)

logger = logging.getLogger(__name__)


class HuggingFaceStorageService:
    """
    Centralized production service for interacting with Hugging Face Hub.
    - Datasets: ankush0710/hdfc-llm-datasets
    - Models:   ankush0710/hdfc-llm-models
    """

    def __init__(
        self,
        token: Optional[str] = None,
        dataset_repo: Optional[str] = None,
        model_repo: Optional[str] = None,
        temp_dir: Optional[Union[str, Path]] = None,
    ):
        self.token = token or HF_TOKEN
        self.dataset_repo = dataset_repo or HF_DATASET_REPO or "ankush0710/hdfc-llm-datasets"
        self.model_repo = model_repo or HF_MODEL_REPO or "ankush0710/hdfc-llm-models"
        self.temp_dir = Path(temp_dir or HF_LOCAL_TEMP_DIR).resolve()
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._api: Optional[HfApi] = None

    @property
    def api(self) -> HfApi:
        """Lazy initialization of HfApi with token."""
        if self._api is None:
            self._api = HfApi(token=self.token)
        return self._api

    # ──────────────────────────────────────────────────────────────────────────
    # DATASET OPERATIONS
    # ──────────────────────────────────────────────────────────────────────────

    def upload_dataset(
        self,
        file_path_or_bytes: Union[str, Path, bytes, io.BytesIO],
        filename: str,
        dataset_id: Union[int, str],
        version: str,
        category: str = "raw",
        commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Uploads a dataset file to the Hugging Face dataset repository.
        Standard path: datasets/{category}/{dataset_id}/v{version}/{filename}
        """
        clean_version = str(version).strip().lstrip("v")
        clean_filename = os.path.basename(filename)
        path_in_repo = f"datasets/{category}/{dataset_id}/v{clean_version}/{clean_filename}"

        if not commit_message:
            commit_message = f"Upload {category} dataset #{dataset_id} v{clean_version} ({clean_filename})"

        logger.info(
            "Uploading dataset to HF: repo='%s', path='%s'",
            self.dataset_repo,
            path_in_repo,
        )

        try:
            # Handle bytes/fileobj vs file path
            if isinstance(file_path_or_bytes, (bytes, io.BytesIO)):
                data = (
                    file_path_or_bytes
                    if isinstance(file_path_or_bytes, bytes)
                    else file_path_or_bytes.getvalue()
                )
                commit_info = self.api.upload_file(
                    path_or_fileobj=data,
                    path_in_repo=path_in_repo,
                    repo_id=self.dataset_repo,
                    repo_type="dataset",
                    commit_message=commit_message,
                    token=self.token,
                )
            else:
                p = Path(file_path_or_bytes).resolve()
                if not p.exists():
                    raise FileNotFoundError(f"Local dataset file not found: {p}")
                commit_info = self.api.upload_file(
                    path_or_fileobj=str(p),
                    path_in_repo=path_in_repo,
                    repo_id=self.dataset_repo,
                    repo_type="dataset",
                    commit_message=commit_message,
                    token=self.token,
                )

            commit_hash = getattr(commit_info, "commit_id", None) or getattr(
                commit_info, "oid", None
            )
            hf_url = f"https://huggingface.co/datasets/{self.dataset_repo}/blob/main/{path_in_repo}"

            logger.info("Successfully uploaded dataset to HF. Commit: %s", commit_hash)

            return {
                "huggingface_repo": self.dataset_repo,
                "huggingface_path": path_in_repo,
                "commit_hash": commit_hash,
                "url": hf_url,
            }

        except Exception as exc:
            logger.error("Failed to upload dataset to Hugging Face Hub: %s", exc)
            raise RuntimeError(
                f"Hugging Face dataset upload failed for '{path_in_repo}': {exc}"
            ) from exc

    def download_dataset(
        self,
        path_in_repo: str,
        local_destination: Optional[Union[str, Path]] = None,
        repo_id: Optional[str] = None,
    ) -> Path:
        """
        Downloads a dataset file from Hugging Face Hub to local temporary storage.
        """
        target_repo = repo_id or self.dataset_repo
        logger.info("Downloading dataset from HF: repo='%s', path='%s'", target_repo, path_in_repo)

        try:
            download_dir = (
                Path(local_destination).parent
                if local_destination
                else (self.temp_dir / "datasets")
            )
            download_dir.mkdir(parents=True, exist_ok=True)

            downloaded_path_str = hf_hub_download(
                repo_id=target_repo,
                filename=path_in_repo,
                repo_type="dataset",
                token=self.token,
                local_dir=str(download_dir) if not local_destination else None,
            )

            downloaded_path = Path(downloaded_path_str).resolve()

            if local_destination and downloaded_path != Path(local_destination).resolve():
                dest_p = Path(local_destination).resolve()
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(downloaded_path, dest_p)
                return dest_p

            return downloaded_path

        except Exception as exc:
            logger.error("Failed to download dataset from HF Hub: %s", exc)
            raise RuntimeError(
                f"Failed to download dataset '{path_in_repo}' from HF Hub ({target_repo}): {exc}"
            ) from exc

    # ──────────────────────────────────────────────────────────────────────────
    # MODEL & ADAPTER OPERATIONS
    # ──────────────────────────────────────────────────────────────────────────

    def upload_model(
        self,
        local_dir: Union[str, Path],
        model_name: str,
        version: str,
        run_id: Optional[Union[int, str]] = None,
        commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Uploads model / LoRA adapter artifacts folder to the Hugging Face model repository.
        Standard path: models/{model_name}/v{version}
        """
        local_path = Path(local_dir).resolve()
        if not local_path.exists() or not local_path.is_dir():
            raise FileNotFoundError(f"Model artifacts directory not found: {local_path}")

        clean_version = str(version).strip().lstrip("v")
        clean_model_slug = model_name.strip().replace(" ", "_").lower()
        path_in_repo = f"models/{clean_model_slug}/v{clean_version}"

        if not commit_message:
            commit_message = f"Upload model {model_name} v{clean_version} (Run #{run_id or 'N/A'})"

        logger.info(
            "Uploading model artifacts to HF: repo='%s', path='%s'",
            self.model_repo,
            path_in_repo,
        )

        try:
            commit_info = self.api.upload_folder(
                folder_path=str(local_path),
                path_in_repo=path_in_repo,
                repo_id=self.model_repo,
                repo_type="model",
                commit_message=commit_message,
                token=self.token,
            )

            commit_hash = getattr(commit_info, "commit_id", None) or getattr(
                commit_info, "oid", None
            )
            hf_url = f"https://huggingface.co/{self.model_repo}/tree/main/{path_in_repo}"

            # Calculate total directory size
            total_size_mb = sum(
                f.stat().st_size for f in local_path.rglob("*") if f.is_file()
            ) / (1024 * 1024)

            logger.info("Successfully uploaded model to HF. Commit: %s", commit_hash)

            return {
                "huggingface_repo": self.model_repo,
                "huggingface_path": path_in_repo,
                "commit_hash": commit_hash,
                "model_size_mb": round(total_size_mb, 2),
                "url": hf_url,
            }

        except Exception as exc:
            logger.error("Failed to upload model to Hugging Face Hub: %s", exc)
            raise RuntimeError(
                f"Hugging Face model upload failed for '{path_in_repo}': {exc}"
            ) from exc

    def download_model(
        self,
        path_in_repo: str,
        local_destination: Optional[Union[str, Path]] = None,
        repo_id: Optional[str] = None,
    ) -> Path:
        """
        Downloads model artifacts folder from Hugging Face Hub to local temporary storage.
        """
        target_repo = repo_id or self.model_repo
        logger.info("Downloading model from HF: repo='%s', path='%s'", target_repo, path_in_repo)

        try:
            target_dir = Path(local_destination or (self.temp_dir / "models" / path_in_repo.replace("/", "_"))).resolve()
            target_dir.mkdir(parents=True, exist_ok=True)

            snapshot_download(
                repo_id=target_repo,
                repo_type="model",
                token=self.token,
                allow_patterns=f"{path_in_repo}/*",
                local_dir=str(target_dir),
            )

            # Check if nested inside path_in_repo in local_dir
            nested_path = target_dir / path_in_repo
            if nested_path.exists() and nested_path.is_dir():
                return nested_path

            return target_dir

        except Exception as exc:
            logger.error("Failed to download model from HF Hub: %s", exc)
            raise RuntimeError(
                f"Failed to download model '{path_in_repo}' from HF Hub ({target_repo}): {exc}"
            ) from exc

    # ──────────────────────────────────────────────────────────────────────────
    # VERIFICATION & METADATA HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def verify_file_exists(
        self,
        path_in_repo: str,
        repo_id: Optional[str] = None,
        repo_type: str = "dataset",
    ) -> bool:
        """Verifies whether a file exists in the specified Hugging Face repository."""
        target_repo = repo_id or (self.dataset_repo if repo_type == "dataset" else self.model_repo)
        try:
            return self.api.file_exists(
                repo_id=target_repo,
                filename=path_in_repo,
                repo_type=repo_type,
                token=self.token,
            )
        except Exception as exc:
            logger.warning("Error checking file existence on HF Hub: %s", exc)
            return False

    def clean_temp_storage(self, max_age_hours: int = 24) -> None:
        """Cleans temporary files and folders older than max_age_hours."""
        try:
            if self.temp_dir.exists():
                for item in self.temp_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    elif item.is_file():
                        item.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Error during temp storage cleanup: %s", exc)


# Singleton instance
_hf_storage_service: Optional[HuggingFaceStorageService] = None


def get_hf_storage_service() -> HuggingFaceStorageService:
    """Factory providing singleton HuggingFaceStorageService."""
    global _hf_storage_service
    if _hf_storage_service is None:
        _hf_storage_service = HuggingFaceStorageService()
    return _hf_storage_service
