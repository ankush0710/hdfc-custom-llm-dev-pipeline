\# HDFC Dataset Release



\## Current frozen master dataset



\*\*Release:\*\* v2.0.0-expanded  

\*\*Dataset:\*\* HDFC\_Custom\_LLM\_All\_11\_Datasets\_Unified\_Suite



| Split | Records |

|---|---:|

| Train | 47,476 |

| Validation | 5,934 |

| Test | 5,936 |

| Total | 59,346 |



\## Model lineage



The current Qwen3-0.6B HDFC LoRA model was trained and evaluated using the earlier Release A dataset:



\- Train: 19,476

\- Validation: 2,434

\- Test: 2,436



The current `v2.0.0-expanded` release is the newer frozen master dataset and has \*\*not\*\* been used to retrain the current Qwen3 model.



\## Data-quality status



\- Duplicate record IDs: 0

\- Cross-split record-ID overlap: 0

\- Cross-split content-hash overlap: 0

\- Invalid JSON: 0

\- Missing required fields: 0

\- PII findings in released JSONL: 0



\## Current AI-serving task types



The master dataset contains 9 task types.



The current AI inference service actively supports:



\- `intent\_classification`

\- `sft\_grounded\_generation`

\- `customer\_faq\_qa`

\- `domain\_concept\_qa`



The remaining master-dataset tasks are retained for future/application-specific use.



\## Release metadata



Authoritative release metadata is stored in:



\- `manifests/dataset\_release\_manifest.json`

\- `manifests/dataset\_release\_hashes.txt`



The complete dataset release is maintained separately as the project handoff artifact rather than duplicated unnecessarily inside Git.

