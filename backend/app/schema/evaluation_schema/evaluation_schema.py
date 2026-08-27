from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================= evaluation model ===================================== #
class EvaluationCreate(BaseModel):
    run_id: int
    model_id: int
    test_dataset_id: int
    auto_start: Optional[bool] = True


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


# ============================= evaluation task breakdown ============================== #
class BenchmarkTaskItem(BaseModel):
    task_name: str
    score: float
    category: str


# ============================= evaluation stats ======================================= #
class EvaluationStatsResponse(BaseModel):
    total_evaluations: int
    avg_score: Optional[float] = None       # null when no scored evaluations exist
    avg_score_str: str = "N/A"              # "89.2%" or "N/A"
    success_rate: str = "0.0%"
    evaluations_trend: Optional[str] = None # null when no historical trend data
    success_trend: Optional[str] = None     # null when no historical trend data


# ============================= evaluation response ===================================== #
class EvaluationResponse(BaseModel):
    evaluation_id: int
    display_id: str = "EV-001"
    run_id: int
    model_id: int
    model_name: Optional[str] = None
    base_model: Optional[str] = None
    test_dataset_id: int
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    score: Optional[str] = None
    score_value: Optional[float] = None
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


# ============================= evaluation detail ===================================== #
class EvaluationDetailResponse(BaseModel):
    evaluation_id: int
    display_id: str
    run_id: int
    model_id: int
    model_name: Optional[str] = None
    base_model: Optional[str] = None
    test_dataset_id: int
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    date_formatted: Optional[str] = None
    status: str
    # All metric fields are null until evaluation completes
    overall_score: Optional[float] = None
    overall_score_str: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_trend: Optional[str] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    recall_trend: Optional[str] = None
    f1_score: Optional[float] = None
    f1_trend: Optional[str] = None
    benchmark_breakdown: list[BenchmarkTaskItem] = []
    average_latency_seconds: Optional[float] = None
    critical_safety_failures: int = 0
    total_examples: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
