from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.constants.supported_models import resolve_hf_model_id, SUPPORTED_TRAINING_MODELS

class TrainingRunCreate(BaseModel):
    dataset_version_id: int = Field(gt=0, description="Dataset version ID (must be > 0)")
    base_model: str = Field(..., min_length=1, description="Base model name or internal identifier")
    training_method: str = Field(default="LoRA", description="Training method (LoRA, QLoRA, Full)")
    epochs: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of epochs (1-20)"
    )
    learning_rate: float = Field(
        default=0.0002,
        gt=0,
        description="Learning rate (> 0)"
    )
    batch_size: int = Field(
        default=4,
        ge=1,
        description="Batch size (>= 1)"
    )

    @field_validator("base_model")
    @classmethod
    def validate_and_resolve_base_model(cls, v: str) -> str:
        # Validates against supported models and returns canonical Hugging Face Model ID
        return resolve_hf_model_id(v)

class TrainingRunResponse(BaseModel):
    id: int
    dataset_version_id: int
    base_model: str
    training_method: str
    epochs: int
    learning_rate: float
    batch_size: int
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    job_id: Optional[int] = None
    job_status: Optional[str] = None
    job_progress: Optional[int] = 0
    progress: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)





