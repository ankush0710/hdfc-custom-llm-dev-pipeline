# Unified ChatML SFT Dataset Schema

```json
{
  "record_id": "string",
  "source": "string",
  "task_type": "string",
  "domain": "string",
  "instruction": "string",
  "context": "string",
  "response": "string",
  "messages": [
    {"role": "system", "content": "string"},
    {"role": "user", "content": "string"},
    {"role": "assistant", "content": "string"}
  ],
  "hash": "string (sha256)"
}
```
