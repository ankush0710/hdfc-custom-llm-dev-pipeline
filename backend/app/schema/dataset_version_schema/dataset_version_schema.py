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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)