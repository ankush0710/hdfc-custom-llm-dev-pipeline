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
