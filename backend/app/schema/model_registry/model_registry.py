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
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelOverview(BaseModel):
    base_model: str
    total_parameters: str
    dataset_name: str
    training_date: str


class ModelDeploymentInfo(BaseModel):
    environment: str
    instance_type: str
    endpoint_url: str
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
    deployed_date: str
    accuracy: str
    changes: str


class ModelDetailResponse(BaseModel):
    id: int
    model_name: str
    version: str
    status: str
    description: str
    overview: ModelOverview
    deployment_info: ModelDeploymentInfo
    performance_metrics: ModelPerformanceMetrics
    version_history: list[ModelVersionHistoryItem] = []
    logs: list[str] = []

    model_config = ConfigDict(from_attributes=True)
