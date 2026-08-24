# Task Support Matrix

The master dataset contains all task types below. The current AI inference service actively supports only the four tasks listed as `Yes`.

| task_type | total_records | percentage | master_dataset | current_model_supported | current_api_supported | status |
|---|---:|---:|---|---|---|---|
| account_status_inquiry | 5,000 | 8.4252% | Yes | No | No | Master dataset / future or application-specific task |
| card_servicing | 5,000 | 8.4252% | Yes | No | No | Master dataset / future or application-specific task |
| customer_faq_qa | 2,987 | 5.0332% | Yes | Yes | Yes | Active |
| domain_concept_qa | 1,000 | 1.6850% | Yes | Yes | Yes | Active |
| intent_classification | 13,359 | 22.5104% | Yes | Yes | Yes | Active |
| loan_summary | 5,000 | 8.4252% | Yes | No | No | Master dataset / future or application-specific task |
| profile_extraction | 10,000 | 16.8503% | Yes | No | No | Master dataset / future or application-specific task |
| sft_grounded_generation | 7,000 | 11.7952% | Yes | Yes | Yes | Active |
| transaction_audit | 10,000 | 16.8503% | Yes | No | No | Master dataset / future or application-specific task |

## Current model-serving task subset

The current AI inference service supports exactly:

- `customer_faq_qa`
- `domain_concept_qa`
- `intent_classification`
- `sft_grounded_generation`

## Important lineage note

The master dataset is broader than the current model-serving task subset. Additional task types are retained in the master dataset and are not silently removed.
