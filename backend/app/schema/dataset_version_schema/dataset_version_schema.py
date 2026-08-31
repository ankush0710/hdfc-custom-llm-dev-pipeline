from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DatasetVersionResponse(BaseModel):
    id: int
    dataset_id: int
    version: str
    file_name: str
    file_size: float
    file_type: str
    status: str
    huggingface_repo: str | None = None
    huggingface_path: str | None = None
    commit_hash: str | None = None
    is_safe_for_training: bool | None = False
    pii_scan_status: str | None = "PENDING"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)