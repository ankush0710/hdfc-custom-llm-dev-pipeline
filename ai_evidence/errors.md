# Error Contract

## Actual inference service exceptions

```text
UnknownModelError
ModelDisabledError
UnsupportedTaskError
ModelLoadError
MissingAdapterError
GenerationError
CudaOutOfMemoryError
```

## Recommended API envelope

```json
{
  "success": false,
  "error": {
    "code": "MODEL_LOAD_FAILED",
    "message": "Failed to load model.",
    "details": {},
    "pipeline_step": "MODEL_LOADING",
    "timestamp": "2026-08-19T10:20:00Z",
    "run_id": null,
    "retryable": true
  }
}
```

## Suggested codes

```text
INVALID_INPUT
UNKNOWN_MODEL
MODEL_DISABLED
UNSUPPORTED_TASK
ADAPTER_NOT_FOUND
MODEL_LOAD_FAILED
GENERATION_FAILED
CUDA_OUT_OF_MEMORY
DATASET_NOT_FOUND
DATASET_INVALID
DATASET_VALIDATION_FAILED
INVALID_TRAINING_CONFIG
TRAINING_FAILED
EVALUATION_FAILED
MODEL_REGISTRATION_FAILED
DEPLOYMENT_FAILED
PIPELINE_TIMEOUT
```

The current training script does not expose a public cancellation/retry HTTP API.
