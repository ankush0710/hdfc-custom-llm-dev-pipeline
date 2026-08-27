from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# database schema for processing request 
class ProcessingRequest(BaseModel):
    dataset_version_id: int
    operations: List[str] = ["clean", "remove_duplicate", "detect_pii", "deidentify_pii"]

# database schema for processing result as a response 
class ProcessingResponse(BaseModel):
    job_id: int
    dataset_version_id: int
    status: str
    pii_instances_detected: Optional[int] = 0
    pii_types_detected: Optional[str] = "NONE"
    records_sanitized: Optional[int] = 0
    is_safe_for_training: Optional[bool] = False

# Alias for backward compatibility
ProcessResponse = ProcessingResponse

# database schema for status response of dataset processing 
class ProcessingStatusResponse(BaseModel):
    job_id: int
    dataset_version_id: int
    status: str
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    pii_instances_detected: Optional[int] = 0
    pii_types_detected: Optional[str] = "NONE"
    records_sanitized: Optional[int] = 0
    is_safe_for_training: Optional[bool] = False

# database schema for all metrics response after processing 
class QualityMetricesResponse(BaseModel):
    total_rows: int
    total_columns: int
    duplicate_rows: int
    missing_values: int
    empty_rows: int
    quality_scores: float
    pii_instances_detected: Optional[int] = 0
    pii_types_detected: Optional[str] = "NONE"
    records_sanitized: Optional[int] = 0
    is_safe_for_training: Optional[bool] = False

QualityMetricsResponse = QualityMetricesResponse
