from pydantic import BaseMaodel
from typing import List, Optional

# database schema for processing request 
class ProcessingRequest(BaseModel):
    dataset_id: int
    operations: List[str]

# database schema for processing result as a response 
class ProcessResponse(BaseModel):
    job_id: int
    dataset_id: int
    status: str

# database schema for status response of dataset processing 
class ProcessingStatusResponse(BaseModel):
    job_id: int
    dataset_id: int
    status: str
    output_file: Optional[str] = None
    error_message: Optional[str] = None

# database schema for all metrics response after processing 
class QualityMetricesResponse(BaseModel):
    total_rows: int
    total_columns: int
    duplicate_rows: int
    missing_values: int
    empty_rows: int
    quality_scores: float


