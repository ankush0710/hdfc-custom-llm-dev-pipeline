from pydantic import BaseModel


class InferenceRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7


class InferenceResponse(BaseModel):
    response: str