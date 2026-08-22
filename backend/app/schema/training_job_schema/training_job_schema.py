from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TrainingJobCreate(BaseModel):

    training_run_id: int = Field(gt=0)


class TrainingJobResponse(BaseModel):

    id: int
    training_run_id: int
    status: str
    worker_id: str | None = None
    progress: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )