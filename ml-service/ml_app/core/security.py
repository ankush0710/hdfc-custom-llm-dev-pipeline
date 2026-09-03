"""
ml-service/app/core/security.py

Security middleware/dependency for authenticating internal requests from the Render backend.
Enforces X-ML-Service-Key validation.
"""
from fastapi import Header, HTTPException, status
from .config import ML_SERVICE_API_KEY


def verify_ml_service_key(
    x_ml_service_key: str = Header(..., alias="X-ML-Service-Key", description="Internal API key for ML service"),
) -> str:
    """Validate that the incoming request contains the correct internal API key."""
    if not ML_SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ML Service authentication key is not configured on the server.",
        )
    if x_ml_service_key != ML_SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid X-ML-Service-Key provided.",
        )
    return x_ml_service_key
