from typing import Any, Optional

from pydantic import BaseModel, Field


class AIInferenceRequest(BaseModel):
    model_id: str = "qwen3_0_6b"

    task_type: str = "customer_faq_qa"

    question: str = Field(
        ...,
        min_length=1
    )

    context: Optional[str] = None

    max_new_tokens: int = Field(
        default=256,
        gt=0,
        le=2048
    )

    temperature: float = Field(
        default=0.2,
        gt=0,
        le=2.0
    )

    top_p: float = Field(
        default=0.9,
        gt=0,
        le=1.0
    )

    do_sample: bool = False

    seed: int = 42


class AIInferenceResponse(BaseModel):
    model_id: str

    model_name: str

    fine_tuned: bool

    task_type: str

    question: str

    context: Optional[str]

    response: Any

    raw_response: str

    latency_seconds: Optional[float]

    device: Optional[str]


class AIModelResponse(BaseModel):
    id: str
    name: str
    fine_tuned: bool
    adapter_available: bool
    enabled: bool
    currently_loaded: bool