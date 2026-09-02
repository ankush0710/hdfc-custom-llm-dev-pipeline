# Logging Contract

The ML layer can generate technical logs; FastAPI decides which sanitized logs are exposed to the frontend.

## Required fields
- run_id
- step
- timestamp
- level
- message

## Levels
```text
DEBUG
INFO
WARNING
ERROR
```

## Example
```json
{
  "run_id": "run-123",
  "step": "TRAINING",
  "timestamp": "2026-08-19T10:20:00Z",
  "level": "INFO",
  "message": "Epoch 1 completed"
}
```

Never expose credentials, tokens, secrets, PII, confidential prompts, or sensitive stack traces to the frontend.
