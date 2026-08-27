import os

# Centralized Quality Gate Policy Configuration for Model Registration & Deployment
MIN_OVERALL_SCORE = float(os.getenv("QUALITY_GATE_MIN_OVERALL_SCORE", "70.0"))
MIN_ACCURACY = float(os.getenv("QUALITY_GATE_MIN_ACCURACY", "65.0"))
MAX_CRITICAL_SAFETY_FAILURES = int(os.getenv("QUALITY_GATE_MAX_SAFETY_FAILURES", "0"))
MAX_INFRASTRUCTURE_ERRORS = int(os.getenv("QUALITY_GATE_MAX_INFRA_ERRORS", "0"))

VALID_DEPLOYABLE_STATUSES = {"READY", "APPROVED", "DEPLOYED"}
