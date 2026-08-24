# Data Preparation Pipeline Specification (As-Built)

1. **Ingestion**: Reads 11 Excel workbooks with task-specific normalization.
2. **Sanitization**: Literal character substitution for UTF-8 encoding cleanup and regex PII masking.
3. **Deduplication**: SHA-256 hash collision tracking.
4. **Splitting**: Deterministic 80/10/10 random shuffle (seed=42).
