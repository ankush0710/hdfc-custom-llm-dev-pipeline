# Evaluation

## Held-out dataset

```text
Test examples: 2,436
```

Run:

```powershell
python -m ai.evaluation.evaluate_finetuned
```

Options:

```text
--device {auto,cuda,cpu}
--limit N
--output-dir PATH
```

## Latest validated full-run snapshot

```text
Intent JSON validity:         1.0000
Intent structured accuracy:   0.8290
Structured answer accuracy:   1.0000
Citation accuracy:            0.0000
Policy flag accuracy:         1.0000
Escalation accuracy:          1.0000
Full structured match:        0.0000
Free-form normalized exact:   0.2215
Critical safety failures:     0
Infrastructure errors:        0
Average latency:              ~3.83 s
```

`normalized_exact_match` is an exact/normalized text metric, not semantic similarity.

Citation accuracy was 0% in the latest full evaluation, so generated citation IDs should not be treated as authoritative without a separate retrieval/source layer.

Critical safety failures were 0.

See the supplied `evaluation-response.json` and `latest_evaluation_snapshot.json` evidence files in this package. If schema documentation is maintained separately, link to the repository location from the final project documentation.
