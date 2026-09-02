# AI Integration Guide — Member 3

## Main integration boundary

Use `ai/inference/service.py` from the backend. The frontend should call the backend API, not Python model code directly.

```python
from ai.inference.service import run_model

result = run_model(
    model_id="qwen3_0_6b",
    task_type="intent_classification",
    question="Can I get another card?",
)
```

## Available models

| ID | Model | HDFC fine-tuned |
|---|---|---|
| `qwen3_0_6b` | Qwen/Qwen3-0.6B | Yes — LoRA |
| `qwen2_5_1_5b_instruct` | Qwen/Qwen2.5-1.5B-Instruct | No |
| `smollm2_1_7b_instruct` | HuggingFaceTB/SmolLM2-1.7B-Instruct | No |

Only Qwen3 uses `ai/artifacts/full_training` as its adapter.

## Supported tasks

- `intent_classification`
- `sft_grounded_generation`
- `customer_faq_qa`
- `domain_concept_qa`

## Response contract

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

`response` can be a dictionary for valid structured JSON output or a string for normal text output. Always check its type. `raw_response` preserves the original generated text.

## Model switching

The tested hardware has 4 GB VRAM. The service is designed to keep only one model loaded at a time and unload the previous model when switching.

## Suggested API

```text
POST /api/inference
```

Example request:

```json
{
  "model_id": "qwen3_0_6b",
  "task_type": "intent_classification",
  "question": "Can I get another card?",
  "context": null,
  "max_new_tokens": 128
}
```

The backend passes the request to `run_model()` and returns the result.

## Safety/evaluation note

The latest Qwen3 held-out evaluation used 2,436 records. Intent JSON validity was 100%, intent structured accuracy was 82.90%, structured answer accuracy was 100%, policy flag accuracy was 100%, escalation accuracy was 100%, critical safety failures were 0, and infrastructure errors were 0. Citation accuracy was 0%, so generated citation IDs must not be treated as authoritative without an external retrieval/source layer.

## Do not

- attach the Qwen3 adapter to Qwen2.5 or SmolLM2
- load all three models simultaneously on a 4 GB GPU
- expose `.safetensors` files to the browser
- call training code from the frontend
- assume every `response` is a string
- treat generated citation IDs as authoritative
- commit `.venv`, caches, raw datasets, or temporary files
