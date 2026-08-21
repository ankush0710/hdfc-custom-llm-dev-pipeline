from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TrainingRunCreate(BaseModel):

    dataset_version_id: int
    base_model: str
    training_method:str
    epochs:int = Field(
        default=3,
        ge=1,
        le=20
    )
    learning_rate:float = Field(
        default=0.0002,
        gt=0
    )
    batch_size:int = Field(
        default=4,
        ge=1
    )

class TrainingRunResponse(BaseModel):

    id:int
    datase_version_id:int
    base_model:str
    training_method:str
    epoch:int
    learning_rate:float
    batch_size:int
    status:str
    error_message:str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)




