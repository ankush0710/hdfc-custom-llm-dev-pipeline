from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


SUPPORTED_TASK_TYPES = {
    "customer_faq_qa",
    "domain_concept_qa",
    "intent_classification",
    "sft_grounded_generation",
}


class InferenceRequest(BaseModel):
    model_id: Union[int, str]
    task_type: str = "sft_grounded_generation"

    question: str = Field(
        ...,
        min_length=1,
    )
    prompt: Optional[str] = None

    context: Optional[str] = None

    max_new_tokens: int = Field(
        default=256,
        gt=0,
        le=1024,
    )

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
    )

    top_p: float = Field(
        default=0.9,
        gt=0.0,
        le=1.0,
    )

    do_sample: bool = False

    seed: int = 42

    @model_validator(mode="after")
    def validate_request_fields(self):
        if not self.question and not self.prompt:
            raise ValueError("Either 'question' or 'prompt' must be provided.")
        if not self.question and self.prompt:
            self.question = self.prompt
        if self.task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(
                f"The selected task type '{self.task_type}' is not supported. "
                f"Supported task types: {', '.join(sorted(SUPPORTED_TASK_TYPES))}"
            )
        return self


class InferenceResponse(BaseModel):
    model_id: Union[int, str]
    model_name: str
    fine_tuned: bool
    task_type: str

    question: str
    context: Optional[str] = None

    response: Any
    raw_response: str

    latency_seconds: Optional[float] = None
    tokens_generated: Optional[int] = None
    device: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)