# Data Preparation

Completed processing flow:

1. Source dataset ingestion
2. Cleaning / structure normalization
3. Encoding cleanup
4. PII detection/redaction
5. Duplicate handling
6. Task normalization
7. JSONL formatting
8. Train/validation/test splitting
9. Final audit

Final JSONL quality gate:

```text
Invalid JSON lines: 0
Missing required fields: 0
Empty required text: 0
Duplicate hashes: 0
Unexpected task types: NONE
Encoding corruption: NONE
Possible PII: NONE
Cross-split duplicates: 0
```
