# API Contract

## Python ML service

```python
run_model(
    model_id: str,
    task_type: str,
    question: str,
    context: str | None = None,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    top_p: float = 0.9,
    do_sample: bool = False,
    seed: int = 42,
)
```

Available models:

```text
qwen3_0_6b
qwen2_5_1_5b_instruct
smollm2_1_7b_instruct
```

Available tasks:

```text
intent_classification
sft_grounded_generation
customer_faq_qa
domain_concept_qa
```

## Common result

```json
{
  "model_id": "qwen3_0_6b",
  "model_name": "Qwen/Qwen3-0.6B",
  "fine_tuned": true,
  "task_type": "intent_classification",
  "question": "Can I get another card?",
  "context": null,
  "response": {
    "intent_category": "getting_spare_card"
  },
  "raw_response": "{\"intent_category\": \"getting_spare_card\"}",
  "latency_seconds": 1.479,
  "device": "cuda"
}
```

`response` can be a dict for valid JSON output or a normal string for free-form text. `raw_response` always preserves the original generated string.

## Recommended FastAPI endpoints

```text
GET  /api/v1/models
GET  /api/v1/models/{model_id}
POST /api/v1/inference

GET  /api/v1/datasets
GET  /api/v1/datasets/{dataset_id}
POST /api/v1/datasets
DELETE /api/v1/datasets/{dataset_id}

POST /api/v1/runs
GET  /api/v1/runs
GET  /api/v1/runs/{run_id}
POST /api/v1/runs/{run_id}/cancel

POST /api/v1/training
GET  /api/v1/training/{run_id}

GET /api/v1/evaluations/{run_id}
```

The Python ML service is not currently a FastAPI server. FastAPI should wrap it.

## HTTP mapping recommendation

```text
200 success
400 invalid input / unsupported task
404 model or adapter not found
409 model disabled
422 invalid training configuration
500 generation/training/evaluation failure
503 model load / CUDA OOM / service unavailable
```

## Long-running jobs

Do not keep a browser request open for the whole training/evaluation operation.

Recommended:

```text
POST /api/v1/runs
    ↓
{ "run_id": "...", "status": "QUEUED" }
    ↓
GET /api/v1/runs/{run_id}
```

Polling is sufficient for the first integration.
