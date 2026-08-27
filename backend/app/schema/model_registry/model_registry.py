from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Model_Create(BaseModel):
    model_name: str
    version: str
    base_model: str
    artifact_path: Optional[str] = None
    adapter_path: Optional[str] = None
    training_job_id: Optional[int] = None
    evaluation_id: Optional[int] = None
    status: Optional[str] = "CREATED"



class Model_Update_Status(BaseModel):
    status: str


class Model_Response(BaseModel):
    id: int
    model_name: str
    version: str
    base_model: str
    artifact_path: Optional[str] = None
    adapter_path: Optional[str] = None
    training_job_id: Optional[int] = None
    evaluation_id: Optional[int] = None
    accuracy: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelOverview(BaseModel):
    base_model: str
    total_parameters: str
    dataset_name: Optional[str] = None     # null when no training job linked
    training_date: Optional[str] = None    # null when no created_at timestamp


class ModelDeploymentInfo(BaseModel):
    environment: str
    instance_type: Optional[str] = None    # not stored in DB
    endpoint_url: Optional[str] = None     # null when model not deployed yet
    status: str


class ModelPerformanceMetrics(BaseModel):
    accuracy: Optional[str] = None
    accuracy_trend: Optional[str] = None
    f1_score: Optional[str] = None
    f1_trend: Optional[str] = None
    latency_ms: Optional[str] = None
    throughput_req_s: Optional[str] = None
    last_evaluated: Optional[str] = None


class ModelVersionHistoryItem(BaseModel):
    id: int
    version: str
    status: str
    deployed_date: Optional[str] = None    # null when no created_at
    accuracy: Optional[str] = None         # null for non-current versions (no eval data)
    changes: Optional[str] = None          # not stored in DB


class ModelDetailResponse(BaseModel):
    id: int
    model_name: str
    version: str
    status: str
    description: Optional[str] = None      # not stored in DB
    overview: ModelOverview
    deployment_info: ModelDeploymentInfo
    performance_metrics: ModelPerformanceMetrics
    version_history: list[ModelVersionHistoryItem] = []
    logs: list[str] = []

    model_config = ConfigDict(from_attributes=True)
