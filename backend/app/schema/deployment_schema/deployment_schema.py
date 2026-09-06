from datetime import datetime
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict


class Deployment_Create(BaseModel):
    model_id: int
    version: str
    environment: str = "development"


class Deployment_Response(BaseModel):
    id: int
    model_id: int
    model_name: str | None = None
    base_model: str | None = None
    version: str
    environment: str
    status: str
    endpoint: str | None = None
    average_latency_ms: float | None = None
    latency: str | None = None
    dataset_name: str | None = None
    dataset_version: str | None = None
    dataset_file_name: str | None = None
    training_run_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Deployment_Status_Response(BaseModel):
    id: int
    status: str
    endpoint: str | None = None