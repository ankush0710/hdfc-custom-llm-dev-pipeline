from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schema.dataset_version_schema.dataset_version_schema import DatasetVersionResponse

class DatasetResponse(BaseModel):
    id: int
    dataset_name: str
    category: str
    source: str
    description: str | None
    versions: list[DatasetVersionResponse] = Field(
        default_factory=list
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


