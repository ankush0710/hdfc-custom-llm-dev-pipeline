from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DatasetResponse(BaseModel):
    id: int
    dataset_name: str
    category: str
    version: str
    source: str
    description: str | None

    file_name: str
    file_size: float
    file_type: str
    
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)




