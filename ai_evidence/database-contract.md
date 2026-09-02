# Database Contract — ML/AI Fields

This defines the ML-side fields that FastAPI/PostgreSQL should persist. The backend owns table design, migrations and constraints.

## Dataset
- dataset_id: string/UUID
- dataset_name: string
- version: string
- category: string/null
- format: string
- record_count: integer
- created_at: ISO-8601 timestamp
- status: string
- quality_score: number/null

## DatasetVersion
- dataset_version_id: string/UUID
- dataset_id: string/UUID
- version: string
- source_reference: string/null
- record_count: integer
- validation_status: string
- created_at: ISO-8601 timestamp

## PipelineRun
- run_id: string/UUID
- dataset_id: string/UUID/null
- dataset_version_id: string/UUID/null
- model_id: string/null
- status: string
- progress: integer/null (0-100)
- current_step: string/null
- started_at: ISO-8601 timestamp/null
- completed_at: ISO-8601 timestamp/null
- estimated_completion: ISO-8601 timestamp/null
- error_code: string/null

## TrainingRun
- training_run_id: string/UUID
- run_id: string/UUID
- base_model: string
- training_method: string
- epochs: number
- learning_rate: number
- batch_size: integer
- gradient_accumulation_steps: integer
- max_sequence_length: integer
- lora_r: integer
- lora_alpha: integer
- lora_dropout: number
- seed: integer
- global_step: integer/null
- train_loss: number/null
- runtime_seconds: number/null
- peak_gpu_memory_mb: number/null
- created_at: ISO-8601 timestamp

## Evaluation
- evaluation_id: string/UUID
- run_id: string/UUID
- model_id: string
- test_dataset_id: string/UUID/null
- total_examples: integer
- intent_json_validity: number/null
- intent_structured_accuracy: number/null
- answer_accuracy: number/null
- citation_accuracy: number/null
- policy_flag_accuracy: number/null
- escalation_accuracy: number/null
- full_structured_match: number/null
- normalized_exact_match: number/null
- critical_safety_failures: integer/null
- infrastructure_errors: integer/null
- average_latency_seconds: number/null
- evaluation_status: string
- created_at: ISO-8601 timestamp

## Model
- model_id: string
- model_name: string
- family: string/null
- base_model: string/null
- fine_tuned: boolean
- status: string
- created_at: ISO-8601 timestamp

## ModelVersion
- model_version_id: string/UUID
- model_id: string
- version: string
- training_run_id: string/UUID/null
- dataset_version_id: string/UUID/null
- evaluation_id: string/UUID/null
- artifact_reference: string/null
- approval_status: string/null
- deployment_status: string/null
- created_at: ISO-8601 timestamp

## PipelineArtifact
- artifact_id: string/UUID
- run_id: string/UUID
- artifact_type: string
- artifact_reference: string
- size_bytes: integer/null
- checksum: string/null
- created_at: ISO-8601 timestamp

## PipelineLog
- log_id: string/UUID
- run_id: string/UUID
- step: string
- timestamp: ISO-8601 timestamp
- level: string
- message: string

Never persist secrets, credentials, or unnecessary PII.
