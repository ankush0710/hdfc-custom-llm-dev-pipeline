from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================= evaluation model ===================================== #
class EvaluationCreate(BaseModel):
    run_id: int
    model_id: int
    test_dataset_id: int


# ============================= evaluation metrics ===================================== #
class EvaluationResult(BaseModel):
    total_examples: int = Field(default=0, ge=0)
    intent_json_validity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    intent_structured_accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    answer_accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    citation_accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    policy_flag_accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    escalation_accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    full_structured_match: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    normalized_exact_match: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    critical_safety_failures: Optional[int] = Field(default=0, ge=0)
    infrastructure_errors: Optional[int] = Field(default=0, ge=0)
    average_latency_seconds: Optional[float] = Field(default=None, ge=0.0)


# ============================= evaluation response ===================================== #
class EvaluationResponse(BaseModel):
    evaluation_id: int
    run_id: int
    model_id: int
    test_dataset_id: int
    total_examples: int = 0
    intent_json_validity: Optional[float] = None
    intent_structured_accuracy: Optional[float] = None
    answer_accuracy: Optional[float] = None
    citation_accuracy: Optional[float] = None
    policy_flag_accuracy: Optional[float] = None
    escalation_accuracy: Optional[float] = None
    full_structured_match: Optional[float] = None
    normalized_exact_match: Optional[float] = None
    critical_safety_failures: Optional[int] = None
    infrastructure_errors: Optional[int] = None
    average_latency_seconds: Optional[float] = None
    evaluation_status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
