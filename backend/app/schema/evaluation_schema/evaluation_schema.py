from datetime import datetime
from typing import Optional
from pydantic import (BaseModel, ConfigDict, Field)


# ============================= eveluation model ===================================== #
class EvaluationModel(BaseModel):
    run_id: int
    model_id:int
    test_dataset_id:int


# ============================= eveluation metrics ===================================== #
class EvaluationResult(BaseModel):
    total_example: int = Field(ge=0)
    intent_json_validity:Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    intent_structured_accuracy: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    answer_accuracy: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    citation_accuracy: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    policy_flag_accuracy: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    escalation_accuracy: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    full_structured_match: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    normalized_exact_match: Optional[float] = Field(ge=0.0, le=1.0, nullable=True)
    average_latency_seconds: Optional[float] = Field(ge=0.0, nullable=True)


# ============================= eveluation response ===================================== 
class EvaluationResponse(BaseModel):
    evaluation_id:int
    run_id:int
    model_id:int
    test_dataset_id:int
    total_examples: int
    intent_json_validity: Optional[float]
    intent_structured_accuracy: Optional[float]
    answer_accuracy: Optional[float]
    citation_accuracy: Optional[float]
    policy_flag_accuracy: Optional[float]
    escalation_accuracy: Optional[float]
    full_structured_match: Optional[float]
    normalized_exact_match: Optional[float]
    critical_safety_failures: Optional[int]
    infrastructure_errors: Optional[int]
    average_latency_seconds: Optional[float]
    evaluation_status: str
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )