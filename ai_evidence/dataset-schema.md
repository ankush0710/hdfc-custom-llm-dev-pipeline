# Dataset Schema

## Core training/evaluation record

```json
{
  "record_id": "string",
  "task_type": "string",
  "instruction": "string",
  "context": "string|null",
  "response": "string",
  "messages": [
    {"role": "system|user|assistant", "content": "string"}
  ]
}
```

Evaluation requires `record_id`, `task_type`, and `response`. Training records additionally carry instruction/context/messages used to build the model input.

## Task types

```text
intent_classification
sft_grounded_generation
customer_faq_qa
domain_concept_qa
```

## Final split

```text
Train: 19,476
Validation: 2,434
Test: 2,436
```

## Validation rules

The audit layer checks:

- invalid JSON lines
- required fields
- empty required text
- duplicate hashes
- unexpected task types
- encoding corruption
- possible email/phone PII
- cross-split duplicates

Final audited JSONL reported zero failures/hits for all listed checks and zero cross-split duplicates.

## Dataset metadata

```json
{
  "dataset_id": "string/uuid",
  "dataset_name": "string",
  "version": "string",
  "category": "string",
  "format": "jsonl",
  "size": 0,
  "created_at": "ISO-8601 timestamp"
}
```

Raw/cleaned Excel corpora remain outside this application handoff package.
