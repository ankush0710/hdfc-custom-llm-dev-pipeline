# Pipeline Status

## Pipeline/training states

```text
CREATED
VALIDATING
PREPROCESSING
TRAINING
EVALUATING
REGISTERING
READY
FAILED
CANCELLED
```

## Inference states

```text
LOADING_MODEL
GENERATING
COMPLETED
FAILED
```

The current Python service performs model loading/generation synchronously. Persistent run-state and queue handling belong to FastAPI/orchestration.
