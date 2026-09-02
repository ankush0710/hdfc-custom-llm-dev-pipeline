# HDFC Bank Custom LLM Development Pipeline — API Contract

> **Authoritative Production API Specification**  
> **Backend Framework:** FastAPI / Python  
> **API Version:** `1.0.0`  
> **Documentation Standard:** OpenAPI 3.1 / GitHub Markdown  

---

## 📌 Table of Contents

1. [Overview](#1-overview)
2. [Base URL & Environments](#2-base-url--environments)
3. [Authentication Architecture](#3-authentication-architecture)
4. [Authorization & Role-Based Access Control (RBAC)](#4-authorization--role-based-access-control-rbac)
5. [Common Request Standards](#5-common-request-standards)
6. [Common Response & Error Standards](#6-common-response--error-standards)
7. [System & Health Endpoints](#7-system--health-endpoints)
8. [Authentication APIs (`/auth`)](#8-authentication-apis-auth)
9. [Dataset Management APIs (`/datasets`)](#9-dataset-management-apis-datasets)
10. [Data Processing & Quality APIs (`/data-processing`)](#10-data-processing--quality-apis-data-processing)
11. [Model Training APIs (`/training`)](#11-model-training-apis-training)
12. [Training Jobs APIs (`/training-jobs`)](#12-training-jobs-apis-training-jobs)
13. [Model Evaluation APIs (`/evaluations`)](#13-model-evaluation-apis-evaluations)
14. [Model Registry APIs (`/models`)](#14-model-registry-apis-models)
15. [Model Deployment APIs (`/deployments`)](#15-model-deployment-apis-deployments)
16. [Inference APIs (`/inference`)](#16-inference-apis-inference)
17. [Direct AI Inference APIs (`/ai`)](#17-direct-ai-inference-apis-ai)
18. [Pipeline Lineage & Dashboard APIs (`/pipeline`)](#18-pipeline-lineage--dashboard-apis-pipeline)
19. [HTTP Status Code Reference](#19-http-status-code-reference)
20. [Frontend Integration Guidelines](#20-frontend-integration-guidelines)
21. [Complete API Endpoint Summary Table](#21-complete-api-endpoint-summary-table)

---

# 1. Overview

The **HDFC Bank Custom LLM Development Pipeline API** provides a governed, enterprise-grade backend service for managing the complete lifecycle of domain-specific Large Language Models (LLMs).

### Key Architectural Capabilities:
* **Dataset Management:** Multi-format dataset ingestion (`.csv`, `.xlsx`, `.json`, `.jsonl`), versioning, and Hugging Face Hub dataset syncing.
* **Data Processing:** PII scanning, sanitization/de-identification, deduplication, and data quality scoring.
* **Model Training:** Parameter-Efficient Fine-Tuning (PEFT / LoRA / QLoRA) orchestration with step-level live metric tracking.
* **Model Evaluation:** Multi-dimensional benchmark scoring, intent validity, structured accuracy, safety failure checks, and latency measurements.
* **Model Registry & Deployment:** Formal model lifecycle state machine (`CREATED`, `READY`, `ACTIVE`, `FAILED`, `ARCHIVED`) with rollback, reload, and runtime serving.
* **Enterprise Security:** JWT-based stateless authentication, bcrypt password hashing, and granular 4-tier Role-Based Access Control (RBAC).

---

# 2. Base URL & Environments

| Environment | Base URL | Interactive API Docs |
| :--- | :--- | :--- |
| **Local Development** | `http://localhost:8000` | Swagger UI: `http://localhost:8000/docs`<br/>ReDoc: `http://localhost:8000/redoc` |
| **Production** | *Configured via host deployment (e.g., Render/AWS)* | *Disabled by default when `ENVIRONMENT=production`* |

> **CORS Policy:** Allowed development origins include `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`, and `http://127.0.0.1:3001`. Production environments require explicit origin configuration via the `ALLOW_ORIGIN` environment variable.

---

# 3. Authentication Architecture

The API uses **JSON Web Tokens (JWT)** with the `HS256` HMAC-SHA256 signature algorithm.

### Authentication Mechanism:
1. Users authenticate via `POST /auth/login` by supplying their email and password.
2. The server validates credentials against the bcrypt password hash in Neon PostgreSQL and returns a signed `access_token` (`token_type: "bearer"`).
3. The client includes the token in the HTTP `Authorization` header for all protected endpoints:
   ```http
   Authorization: Bearer <access_token>
   ```
4. Default token lifespan: **1440 minutes (24 hours)** (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
5. **Token Payload (`sub`):** Stores the user ID (`int`), email (`str`), and role (`str`).

---

# 4. Authorization & Role-Based Access Control (RBAC)

The backend implements role-based access control via the `require_roles(*allowed_roles)` dependency.

### Defined Roles (`VALID_ROLES`):

| Role Identifier | Display Name | Access Scope & Permissions |
| :--- | :--- | :--- |
| **`ADMIN`** | System Administrator | **Full system access.** Manages users, modifies user roles, activates/deactivates accounts, uploads datasets, triggers training, evaluation, and deployments. |
| **`DS`** *(or `DATA_SCIENTIST`)* | Data Scientist | Full AI/ML pipeline access. Uploads/deletes datasets, starts data processing, initiates training runs, registers models, creates evaluations, and triggers deployments. |
| **`REVIEWER`** | Quality Reviewer | Model quality & governance access. Can view datasets and training runs, create and run evaluation jobs, and update model statuses. |
| **`VIEWER`** | Read-Only Viewer | Read-only access to all dashboards, dataset versions, training progress, evaluation metrics, and model registry records. Can run inference queries. |

---

# 5. Common Request Standards

### Headers:
* `Content-Type: application/json` for standard JSON endpoints.
* `Content-Type: multipart/form-data` for file upload endpoints (`/datasets/upload-dataset`).
* `Authorization: Bearer <token>` for all authenticated endpoints.

---

# 6. Common Response & Error Standards

### Standard Validation Error (`422 Unprocessable Entity`):
FastAPI returns detailed validation error arrays when request payloads fail schema validation:
```json
{
  "detail": [
    {
      "loc": ["body", "dataset_version_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Standard Application Error Response (`400`, `401`, `403`, `404`, `500`, `503`):
```json
{
  "detail": "Descriptive error message indicating the failure reason."
}
```

---

# 7. System & Health Endpoints

### `GET /`
* **Description:** API root status check.
* **Authentication:** Not required
* **Response (200 OK):**
```json
{
  "message": "HDFC Custom LLM Pipeline API is running",
  "environment": "development"
}
```

---

### `GET /health`
* **Description:** Liveness probe for container orchestration and load balancers. Validates database connectivity with `SELECT 1`.
* **Authentication:** Not required
* **Response (200 OK / 503 Service Unavailable):**
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

# 8. Authentication APIs (`/auth`)

### `POST /auth/signup`
* **Description:** Register a new platform user account.
* **Authentication:** Not required
* **HTTP Status:** `201 Created`

#### Request Body (`UserSignup`):
| Field | Type | Required | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `full_name` | `string` | **Yes** | — | `min_length: 2`, `max_length: 255` | Full name of the user |
| `email` | `string (email)` | **Yes** | — | Valid email address | User login email |
| `password` | `string` | **Yes** | — | `min_length: 8`, `max_length: 128` | Plaintext password |
| `confirm_password` | `string` | **Yes** | — | Must match `password` | Confirmation password |
| `role` | `string` | No | `"DS"` | `"ADMIN"`, `"DS"`, `"REVIEWER"`, `"VIEWER"` | Initial role assignment |

#### Success Response (201 Created):
```json
{
  "id": 1,
  "full_name": "Ankush Kurvey",
  "email": "ankush@example.com",
  "role": "DS",
  "is_active": true,
  "created_at": "2026-09-02T10:00:00Z"
}
```

---

### `POST /auth/login`
* **Description:** Authenticate using email and password to receive a JWT Bearer token.
* **Authentication:** Not required
* **HTTP Status:** `200 OK`

#### Request Body (`UserLogin`):
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `email` | `string (email)` | **Yes** | Registered user email |
| `password` | `string` | **Yes** | User password |

#### Success Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "full_name": "Ankush Kurvey",
    "email": "ankush@example.com",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2026-09-02T10:00:00Z"
  }
}
```

---

### `GET /auth/me`
* **Description:** Retrieve the profile details of the currently authenticated user.
* **Authentication:** Required (`Bearer Token`)
* **Roles:** All authenticated users
* **Response (200 OK):** `UserResponse` object.

---

### `POST /auth/logout`
* **Description:** Acknowledge session logout for the active user.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):**
```json
{
  "message": "Logged out successfully",
  "user_id": 1
}
```

---

### `GET /auth/users`
* **Description:** List all registered platform users ordered by creation date descending.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN` only
* **Response (200 OK):** `List[UserResponse]`

---

### `PUT /auth/users/{user_id}/role`
* **Description:** Update a user's authorization role. Prevents demoting the sole active system administrator.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN` only

#### Request Body (`RoleUpdate`):
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `role` | `string` | **Yes** | `"ADMIN"`, `"DS"`, `"REVIEWER"`, `"VIEWER"` |

#### Response (200 OK): `UserResponse` object with updated role.

---

### `PATCH /auth/users/{user_id}/status`
* **Description:** Activate or deactivate a user account. Prevents admins from deactivating themselves.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN` only

#### Request Body (`UserStatusUpdate`):
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `is_active` | `boolean` | **Yes** | `true` to activate, `false` to deactivate |

#### Response (200 OK): `UserResponse` object with updated status.

---

# 9. Dataset Management APIs (`/datasets`)

### `POST /datasets/upload-dataset`
* **Description:** Upload and ingest a new dataset file via multipart form. Creates the parent `Dataset_Model` and the initial `Dataset_Version_Model`.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`
* **Supported File Extensions:** `.csv`, `.xlsx`, `.jsonl`, `.json`

#### Form Data Parameters:
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `datasetName` / `dataset_name` | `string` | **Yes** (one required) | Human-readable name of the dataset |
| `category` | `string` | **Yes** | Dataset category (e.g. `"Banking FAQ"`, `"Policies"`) |
| `version` | `string` | **Yes** | Version label (e.g. `"1.0.0"`) |
| `source` | `string` | **Yes** | Data source origin (e.g. `"Internal Documentation"`) |
| `description` | `string` | No | Optional description of the dataset |
| `file` | `UploadFile (binary)` | **Yes** | Raw dataset file binary |

#### Response (200 OK - `DatasetResponse`):
```json
{
  "id": 1,
  "dataset_name": "HDFC Customer FAQs",
  "category": "Customer Support",
  "source": "Branch Ops",
  "description": "Cleaned customer query pairs",
  "versions": [
    {
      "id": 1,
      "dataset_id": 1,
      "version": "1.0.0",
      "file_name": "customer_faqs_v1.csv",
      "file_size": 245760.0,
      "file_type": ".csv",
      "status": "UPLOADED",
      "huggingface_repo": "ankush0710/hdfc-llm-datasets",
      "huggingface_path": "customer_faqs/v1.0.0/customer_faqs_v1.csv",
      "commit_hash": "a1b2c3d4e5",
      "is_safe_for_training": false,
      "pii_scan_status": "PENDING",
      "created_at": "2026-09-02T10:30:00Z"
    }
  ],
  "created_at": "2026-09-02T10:30:00Z",
  "updated_at": "2026-09-02T10:30:00Z"
}
```

---

### `GET /datasets/`
* **Description:** Retrieve all datasets with their associated versions.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** All authenticated users
* **Response (200 OK):** `List[DatasetResponse]`

---

### `GET /datasets/{dataset_id}`
* **Description:** Retrieve a single dataset by ID with full version details.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `DatasetResponse`

---

### `GET /datasets/{dataset_id}/download`
* **Description:** Stream/download the latest file version of a dataset. Resolves from local storage or downloads on-demand from Hugging Face Hub.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** Binary stream (`media_type: application/octet-stream`).

---

### `DELETE /datasets/{dataset_id}`
* **Description:** Delete a dataset and its versions from database and local storage.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`
* **Response (200 OK):**
```json
{
  "message": "Dataset deleted successfully",
  "dataset_id": 1
}
```

---

### `GET /datasets/{dataset_id}/versions`
* **Description:** List all version records for a specific dataset ID.
* **Authentication:** Not required
* **Response (200 OK):** `List[DatasetVersionResponse]`

---

### `GET /datasets/versions/{version_id}/download`
* **Description:** Download the specific dataset file corresponding to `version_id`.
* **Authentication:** Not required
* **Response (200 OK):** Binary file stream (`media_type: application/octet-stream`).

---

# 10. Data Processing & Quality APIs (`/data-processing`)

### `POST /data-processing/jobs`
* **Description:** Trigger an automated data processing pipeline on a dataset version (PII detection, redaction, duplicate removal, and quality calculation).
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`

#### Request Body (`ProcessingRequest`):
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `dataset_version_id` | `integer` | **Yes** | — | Target dataset version ID |
| `operations` | `List[string]` | No | `["clean", "remove_duplicate", "detect_pii", "deidentify_pii"]` | Ordered processing operations |

#### Success Response (200 OK - `ProcessingResponse`):
```json
{
  "job_id": 12,
  "dataset_version_id": 1,
  "status": "COMPLETED",
  "pii_instances_detected": 4,
  "pii_types_detected": "ACCOUNT_NUMBER, PHONE_NUMBER",
  "records_sanitized": 4,
  "is_safe_for_training": true
}
```

---

### `GET /data-processing/jobs/{job_id}`
* **Description:** Retrieve the execution status and output metrics of a data processing job.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `ProcessingStatusResponse`):**
```json
{
  "job_id": 12,
  "dataset_version_id": 1,
  "status": "COMPLETED",
  "output_file": "storage/processed/customer_faqs_v1_sanitized.jsonl",
  "error_message": null,
  "pii_instances_detected": 4,
  "pii_types_detected": "ACCOUNT_NUMBER, PHONE_NUMBER",
  "records_sanitized": 4,
  "is_safe_for_training": true
}
```

---

### `GET /data-processing/versions/{version_id}/metrics`
* **Description:** Retrieve dataset version quality scores, row counts, duplicate metrics, and PII scan status.
* **Authentication:** Not required
* **Response (200 OK):**
```json
{
  "job_id": 12,
  "total_rows": 24346,
  "total_records": 24346,
  "record_count": 24346,
  "total_columns": 6,
  "column_count": 6,
  "duplicate_rows": 0,
  "missing_values": 0,
  "empty_rows": 0,
  "quality_score": 99.4,
  "qualityScore": 99.4,
  "pii_instances_detected": 0,
  "pii_types_detected": "NONE",
  "records_sanitized": 4,
  "is_safe_for_training": true,
  "pii_scan_status": "CLEARED"
}
```

---

# 11. Model Training APIs (`/training`)

### `POST /training/runs`
* **Description:** Create a new training configuration run against a validated dataset version.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`

#### Supported Base Models (`SUPPORTED_TRAINING_MODELS`):
* `qwen2_5_1_5b_instruct` (`Qwen/Qwen2.5-1.5B-Instruct` — 1.54B)
* `qwen3_0_6b` (`Qwen/Qwen3-0.6B` — 0.6B)
* `smollm2_1_7b_instruct` (`HuggingFaceTB/SmolLM2-1.7B-Instruct` — 1.7B)

#### Request Body (`TrainingRunCreate`):
| Field | Type | Required | Default | Validation Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dataset_version_id` | `integer` | **Yes** | — | `gt: 0` | Target dataset version ID |
| `base_model` | `string` | **Yes** | — | Supported model ID or alias | Base model identifier |
| `training_method` | `string` | No | `"LoRA"` | `"LoRA"`, `"QLoRA"`, `"Full"` | Training technique |
| `epochs` | `integer` | No | `3` | `ge: 1`, `le: 20` | Number of training epochs |
| `learning_rate` | `float` | No | `0.0002` | `gt: 0` | Learning rate |
| `batch_size` | `integer` | No | `4` | `ge: 1` | Per-device training batch size |

#### Success Response (200 OK - `TrainingRunResponse`):
```json
{
  "id": 5,
  "dataset_version_id": 1,
  "base_model": "Qwen/Qwen3-0.6B",
  "training_method": "LoRA",
  "epochs": 3,
  "learning_rate": 0.0002,
  "batch_size": 4,
  "status": "CREATED",
  "error_message": null,
  "created_at": "2026-09-02T11:00:00Z",
  "job_id": null,
  "job_status": null,
  "job_progress": 0,
  "progress": 0
}
```

---

### `POST /training/runs/{run_id}/start`
* **Description:** Launch training execution in the background. Creates the low-level `TrainingJobModel` and automatically uploads artifacts to Hugging Face Hub upon completion.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`
* **Response (200 OK):** `TrainingRunResponse` (status updated to `"RUNNING"`).

---

### `POST /training/runs/{run_id}/stop`
* **Description:** Signal a running training execution to stop immediately.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`
* **Response (200 OK):** `TrainingRunResponse` (status updated to `"STOPPED"`).

---

### `GET /training/runs`
* **Description:** List all training runs with live job progress and statuses.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `List[TrainingRunResponse]`

---

### `GET /training/runs/{run_id}`
* **Description:** Get basic training run metadata by ID.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `TrainingRunResponse`

---

### `GET /training/runs/{run_id}/detail`
* **Description:** Get complete enriched training run details including linked dataset info, step counts, training loss, learning rate, and sparkline metric history.
* **Authentication:** Not required
* **Response (200 OK - `TrainingRunDetailResponse`):**
```json
{
  "id": 5,
  "dataset_version_id": 1,
  "dataset_name": "HDFC Customer FAQs",
  "dataset_version_label": "v1.0.0",
  "dataset_row_count": 24346,
  "base_model": "Qwen/Qwen3-0.6B",
  "training_method": "LoRA",
  "epochs": 3,
  "learning_rate": 0.0002,
  "batch_size": 4,
  "status": "COMPLETED",
  "error_message": null,
  "created_at": "2026-09-02T11:00:00Z",
  "started_at": "2026-09-02T11:01:00Z",
  "completed_at": "2026-09-02T11:45:00Z",
  "job_id": 8,
  "job_status": "COMPLETED",
  "job_progress": 100,
  "model_id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "huggingface_repo": "ankush0710/hdfc-llm-models",
  "huggingface_path": "models/hdfc_qwen3_0.6b_run_5/v1.0.0",
  "commit_hash": "f4e3d2c1",
  "training_loss": 0.34215,
  "current_lr": 0.000024,
  "token_accuracy": null,
  "metric_history": [
    { "step": 100, "loss": 1.2451, "lr": 0.00019, "accuracy": null },
    { "step": 500, "loss": 0.3421, "lr": 0.000024, "accuracy": null }
  ]
}
```

---

### `GET /training/runs/{run_id}/logs`
* **Description:** Retrieve formatted execution logs and step progression for terminal views.
* **Authentication:** Not required
* **Response (200 OK - `TrainingRunLogsResponse`):**
```json
{
  "run_id": 5,
  "status": "COMPLETED",
  "error_message": null,
  "job_id": 8,
  "job_status": "COMPLETED",
  "job_progress": 100,
  "logs": [
    { "timestamp": "11:01:00", "level": "INFO", "message": "[11:01:00] Training run #5 started. Base model: Qwen/Qwen3-0.6B | Method: LoRA" },
    { "timestamp": "11:15:30", "level": "INFO", "message": "[11:15:30] Step 250 | 50% | Loss: 0.5420 | LR: 1.00e-04" },
    { "timestamp": "11:45:00", "level": "INFO", "message": "[11:45:00] Training completed successfully." }
  ]
}
```

---

# 12. Training Jobs APIs (`/training-jobs`)

### `GET /training-jobs`
* **Description:** List all underlying worker training jobs.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `List[TrainingJobResponse]`

---

### `GET /training-jobs/{job_id}`
* **Description:** Get specific training worker job by ID.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `TrainingJobResponse`):**
```json
{
  "id": 8,
  "training_run_id": 5,
  "status": "COMPLETED",
  "worker_id": "worker-gpu-0",
  "progress": 100,
  "error_message": null,
  "created_at": "2026-09-02T11:01:00Z",
  "started_at": "2026-09-02T11:01:05Z",
  "completed_at": "2026-09-02T11:45:00Z"
}
```

---

# 13. Model Evaluation APIs (`/evaluations`)

### `POST /evaluations`
* **Description:** Create a new evaluation benchmark run. If `auto_start=True` (default), scoring starts immediately in the background.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`, `REVIEWER`

#### Request Body (`EvaluationCreate`):
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `run_id` | `integer` | **Yes** | — | Associated training run ID |
| `model_id` | `integer` | **Yes** | — | Registered model ID to evaluate |
| `test_dataset_id` | `integer` | **Yes** | — | Test dataset version ID |
| `auto_start` | `boolean` | No | `true` | Auto-launch background evaluation |

#### Success Response (200 OK - `EvaluationResponse`):
```json
{
  "evaluation_id": 3,
  "display_id": "EV-003",
  "run_id": 5,
  "model_id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "base_model": "Qwen/Qwen3-0.6B",
  "test_dataset_id": 1,
  "dataset_name": "HDFC Customer FAQs",
  "dataset_version": "1.0.0",
  "score": "91.5%",
  "score_value": 0.915,
  "total_examples": 28,
  "intent_json_validity": 1.0,
  "intent_structured_accuracy": 0.928,
  "answer_accuracy": 0.915,
  "citation_accuracy": 0.892,
  "policy_flag_accuracy": 1.0,
  "escalation_accuracy": 0.964,
  "full_structured_match": 0.892,
  "normalized_exact_match": 0.892,
  "critical_safety_failures": 0,
  "infrastructure_errors": 0,
  "average_latency_seconds": 12.6,
  "evaluation_status": "COMPLETED",
  "error_message": null,
  "created_at": "2026-09-02T12:00:00Z"
}
```

---

### `GET /evaluations/stats`
* **Description:** Retrieve aggregate evaluation statistics across all completed evaluations.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `EvaluationStatsResponse`):**
```json
{
  "total_evaluations": 12,
  "avg_score": 89.2,
  "avg_score_str": "89.2%",
  "success_rate": "91.7%",
  "evaluations_trend": null,
  "success_trend": null
}
```

---

### `GET /evaluations`
* **Description:** List evaluation runs with optional filtering.
* **Authentication:** Required (`Bearer Token`)
* **Query Parameters:**
  * `run_id` (`integer`, optional): Filter evaluations by training run ID.
* **Response (200 OK):** `List[EvaluationResponse]`

---

### `GET /evaluations/{evaluation_id}`
* **Description:** Retrieve evaluation record by ID.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `EvaluationResponse`

---

### `GET /evaluations/{evaluation_id}/detail`
* **Description:** Retrieve detailed evaluation breakdown for frontend visualization cards and benchmark charts.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `EvaluationDetailResponse`):**
```json
{
  "evaluation_id": 3,
  "display_id": "EV-003",
  "run_id": 5,
  "model_id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "base_model": "Qwen/Qwen3-0.6B",
  "test_dataset_id": 1,
  "dataset_name": "HDFC Customer FAQs",
  "dataset_version": "1.0.0",
  "date_formatted": "Sep 02, 2026",
  "status": "COMPLETED",
  "overall_score": 91.5,
  "overall_score_str": "91.5%",
  "accuracy": 91.5,
  "precision": 92.8,
  "recall": 89.2,
  "f1_score": 90.9,
  "benchmark_breakdown": [
    { "task_name": "FAQ Groundedness", "score": 92.5, "category": "Accuracy" },
    { "task_name": "PII Non-Leakage", "score": 100.0, "category": "Safety" }
  ],
  "average_latency_seconds": 12.6,
  "critical_safety_failures": 0,
  "total_examples": 28,
  "created_at": "2026-09-02T12:00:00Z",
  "completed_at": "2026-09-02T12:06:00Z"
}
```

---

### `POST /evaluations/{evaluation_id}/start`
* **Description:** Manually trigger scoring execution for a created evaluation run.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`, `REVIEWER`
* **Response (200 OK):** `EvaluationResponse`

---

# 14. Model Registry APIs (`/models`)

### `POST /models`
* **Description:** Register a new fine-tuned model / adapter into the Model Registry.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`

#### Request Body (`Model_Create`):
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `model_name` | `string` | **Yes** | — | Unique name of the model |
| `version` | `string` | **Yes** | — | Semantic version (e.g. `"1.0.0"`) |
| `base_model` | `string` | **Yes** | — | Base model identifier |
| `artifact_path` | `string` | No | `null` | Path to weights on disk |
| `adapter_path` | `string` | No | `null` | Path to LoRA adapter |
| `huggingface_repo` | `string` | No | `null` | Hugging Face Hub repository |
| `huggingface_path` | `string` | No | `null` | Hugging Face artifact path |
| `commit_hash` | `string` | No | `null` | Git / HF commit hash |
| `model_size` | `float` | No | `null` | Model size in MB |
| `training_job_id` | `integer` | No | `null` | Source training job ID |
| `evaluation_id` | `integer` | No | `null` | Associated evaluation ID |
| `status` | `string` | No | `"CREATED"` | `"CREATED"`, `"READY"`, `"ACTIVE"`, `"ARCHIVED"` |

#### Response (200 OK - `Model_Response`):
```json
{
  "id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "version": "1.0.0",
  "base_model": "Qwen/Qwen3-0.6B",
  "artifact_path": "storage/models/run_5",
  "adapter_path": "storage/models/run_5/adapter",
  "huggingface_repo": "ankush0710/hdfc-llm-models",
  "huggingface_path": "models/hdfc_qwen3_0.6b_run_5/v1.0.0",
  "commit_hash": "f4e3d2c1",
  "model_size": 1240.5,
  "training_job_id": 8,
  "evaluation_id": 3,
  "accuracy": "91.5%",
  "status": "READY",
  "created_at": "2026-09-02T12:10:00Z",
  "updated_at": "2026-09-02T12:10:00Z"
}
```

---

### `GET /models`
* **Description:** List all registered models with their latest evaluated accuracy.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `List[Model_Response]`

---

### `GET /models/{model_id}`
* **Description:** Retrieve model registry entry by ID.
* **Authentication:** Not required
* **Response (200 OK):** `Model_Response`

---

### `GET /models/{model_id}/detail`
* **Description:** Retrieve rich 360-degree model overview including parameters, linked dataset, active deployment info, evaluation performance metrics, version history, and audit logs.
* **Authentication:** Not required
* **Response (200 OK - `ModelDetailResponse`):**
```json
{
  "id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "version": "v1.0.0",
  "status": "READY",
  "description": null,
  "overview": {
    "base_model": "Qwen/Qwen3-0.6B",
    "total_parameters": "0.5 Billion",
    "dataset_name": "HDFC Customer FAQs (v1.0.0)",
    "training_date": "Sep 02, 2026"
  },
  "deployment_info": {
    "environment": "Production",
    "instance_type": null,
    "endpoint_url": "http://localhost:8000/inference/predict",
    "status": "READY"
  },
  "performance_metrics": {
    "accuracy": "91.5%",
    "accuracy_trend": "+1.2%",
    "f1_score": "0.89",
    "f1_trend": "+0.03",
    "latency_ms": "12600 ms",
    "throughput_req_s": "0 req/s",
    "last_evaluated": "Sep 02, 2026"
  },
  "version_history": [
    {
      "id": 2,
      "version": "v1.0.0",
      "status": "READY",
      "deployed_date": "Sep 02, 2026",
      "accuracy": "91.5%",
      "changes": null
    }
  ],
  "logs": [
    "[Sep 02, 2026 10:00:15] Model 'hdfc_qwen3_0.6b_run_5' (v1.0.0) loaded into registry.",
    "[Sep 02, 2026 10:02:11] Benchmark evaluation accuracy=91.5%, F1=0.89."
  ]
}
```

---

### `PATCH /models/{model_id}/status`
* **Description:** Update model lifecycle status (e.g. promoting from `READY` to `ACTIVE` or `ARCHIVED`).
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`, `REVIEWER`

#### Request Body (`Model_Update_Status`):
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `status` | `string` | **Yes** | New status (`"CREATED"`, `"READY"`, `"ACTIVE"`, `"ARCHIVED"`) |

#### Response (200 OK): `Model_Response`

---

# 15. Model Deployment APIs (`/deployments`)

### `POST /deployments`
* **Description:** Deploy a registered model version to an environment (`development`, `staging`, `production`). Automatically activates model serving endpoint.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`

#### Request Body (`Deployment_Create`):
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `model_id` | `integer` | **Yes** | — | Registered model ID |
| `version` | `string` | **Yes** | — | Model version label |
| `environment` | `string` | No | `"development"` | Target environment |

#### Response (200 OK - `Deployment_Response`):
```json
{
  "id": 1,
  "model_id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "base_model": "Qwen/Qwen3-0.6B",
  "version": "1.0.0",
  "environment": "development",
  "status": "ACTIVE",
  "endpoint": "http://localhost:8000/inference/predict",
  "created_at": "2026-09-02T12:30:00Z",
  "updated_at": null
}
```

---

### `GET /deployments`
* **Description:** List all active and past deployments.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `List[Deployment_Response]`

---

### `GET /deployments/{deployment_id}`
* **Description:** Retrieve deployment details by ID.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** `Deployment_Response`

---

### Deployment Lifecycle Control Endpoints:
All lifecycle endpoints require `ADMIN` or `DS` role:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/deployments/{id}/rollback` | Rollback deployment to the previous stable active version |
| `POST` | `/deployments/{id}/undeploy` | Undeploy and deactivate serving endpoint |
| `POST` | `/deployments/{id}/unload` | Unload active model weights from memory |
| `POST` | `/deployments/{id}/reload` | Reload model weights and configurations |
| `POST` | `/deployments/{id}/restart` | Restart the deployment instance |
| `POST` | `/deployments/{id}/start` | Start an inactive deployment |
| `DELETE` | `/deployments/{id}` | Deactivate and delete deployment record |

---

# 16. Inference APIs (`/inference`)

### `POST /inference/predict`
* **Description:** Execute controlled inference against a database-registered model ID with safety parameters.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** All authenticated users

#### Request Body (`InferenceRequest`):
| Field | Type | Required | Default | Validation Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `model_id` | `integer` or `string` | **Yes** | — | Registered model ID or string | Model identifier |
| `question` | `string` | **Yes** | — | `min_length: 1` | User query (or pass via `prompt`) |
| `prompt` | `string` | No | `null` | — | Alternative query alias |
| `context` | `string` | No | `null` | — | Banking policy / fixture context |
| `task_type` | `string` | No | `"sft_grounded_generation"` | Supported AI task type | Target prompt task |
| `max_new_tokens` | `integer` | No | `256` | `gt: 0`, `le: 1024` | Maximum generated tokens |
| `temperature` | `float` | No | `0.2` | `ge: 0.0`, `le: 2.0` | Sampling temperature |
| `top_p` | `float` | No | `0.9` | `gt: 0.0`, `le: 1.0` | Nucleus sampling probability |
| `do_sample` | `boolean` | No | `false` | — | Whether to sample tokens |
| `seed` | `integer` | No | `42` | — | Reproducibility seed |

#### Success Response (200 OK - `InferenceResponse`):
```json
{
  "model_id": 2,
  "model_name": "hdfc_qwen3_0.6b_run_5",
  "fine_tuned": true,
  "task_type": "sft_grounded_generation",
  "question": "What is the minimum balance required for an HDFC Savings Account?",
  "context": "HDFC Bank Savings Account requires an Average Monthly Balance (AMB) of Rs. 10,000 for Metro branches.",
  "response": {
    "intent": "SAVINGS_ACCOUNT_INQUIRY",
    "answer": "The minimum Average Monthly Balance (AMB) required for an HDFC Regular Savings Account in metro branches is Rs. 10,000.",
    "citations": ["HDFC Master Policy Doc #436"],
    "requires_escalation": false
  },
  "raw_response": "{\"intent\": \"SAVINGS_ACCOUNT_INQUIRY\", ...}",
  "latency_seconds": 0.452,
  "tokens_generated": 64,
  "device": "cuda:0"
}
```

---

### `GET /inference/models`
* **Description:** List all AI models currently loaded and available in the inference runtime.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK):** Dictionary/List of model descriptors.

---

### `POST /inference/unload`
* **Description:** Free GPU/RAM by unloading the active inference model adapter from memory.
* **Authentication:** Required (`Bearer Token`)
* **Allowed Roles:** `ADMIN`, `DS`
* **Response (200 OK):**
```json
{
  "status": "unloaded",
  "message": "Model unloaded successfully from memory"
}
```

---

# 17. Direct AI Inference APIs (`/ai`)

### `POST /ai/generate`
* **Description:** Direct inference endpoint targeting models via internal model keys (e.g. `"qwen3_0_6b"`).
* **Authentication:** Not required
* **HTTP Status:** `200 OK`

#### Request Body (`AIInferenceRequest`):
| Field | Type | Required | Default | Validation Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `model_id` | `string` | No | `"qwen3_0_6b"` | Known model key | Target model key |
| `task_type` | `string` | No | `"customer_faq_qa"` | AI task type | Prompt template task |
| `question` | `string` | **Yes** | — | `min_length: 1` | User query |
| `context` | `string` | No | `null` | — | Optional context |
| `max_new_tokens` | `integer` | No | `256` | `gt: 0`, `le: 2048` | Maximum tokens |
| `temperature` | `float` | No | `0.2` | `gt: 0.0`, `le: 2.0` | Sampling temperature |
| `top_p` | `float` | No | `0.9` | `gt: 0.0`, `le: 1.0` | Top-p nucleus cutoff |
| `do_sample` | `boolean` | No | `false` | — | Sampling flag |
| `seed` | `integer` | No | `42` | — | Seed |

#### Error Conditions:
* `404 Not Found`: `UnknownModelError` (model identifier not recognized).
* `403 Forbidden`: `ModelDisabledError` (model explicitly disabled).
* `400 Bad Request`: `UnsupportedTaskError`.
* `503 Service Unavailable`: `MissingAdapterError` or `CudaOutOfMemoryError`.

---

# 18. Pipeline Lineage & Dashboard APIs (`/pipeline`)

### `GET /pipeline/dashboard/stats`
* **Description:** Real-time aggregate counts, average evaluation scores, and recent activity timeline across datasets, training runs, evaluations, and deployments. Computed directly from PostgreSQL.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `DashboardStatsResponse`):**
```json
{
  "total_datasets": 3,
  "total_models": 4,
  "active_trainings": 1,
  "completed_trainings": 6,
  "failed_trainings": 0,
  "total_evaluations": 5,
  "avg_evaluation_score": 91.2,
  "avg_evaluation_score_str": "91.2%",
  "active_deployments": 2,
  "recent_activity": [
    {
      "id": "run-5",
      "event_type": "training_completed",
      "title": "Training Run #5 Completed",
      "description": "Base model: Qwen/Qwen3-0.6B · Method: LoRA",
      "timestamp": "2026-09-02T11:45:00Z",
      "status": "COMPLETED"
    },
    {
      "id": "eval-3",
      "event_type": "evaluation_completed",
      "title": "Evaluation #3 Completed",
      "description": "Run #5 · 28 examples evaluated",
      "timestamp": "2026-09-02T12:06:00Z",
      "status": "COMPLETED"
    }
  ]
}
```

---

### `GET /pipeline/status/{dataset_version_id}`
* **Description:** Full pipeline lineage snapshot for a given dataset version: `dataset_version → processing_jobs → training_runs → training_jobs → models → evaluations → deployments`.
* **Authentication:** Required (`Bearer Token`)
* **Response (200 OK - `PipelineStatusResponse`):**
```json
{
  "dataset_version": {
    "id": 1,
    "version": "1.0.0",
    "file_name": "customer_faqs_v1.csv",
    "file_type": ".csv",
    "status": "Processed"
  },
  "processing_jobs": [
    { "id": 12, "status": "COMPLETED", "input_file": "uploads/...", "output_file": "storage/..." }
  ],
  "training_runs": [
    { "id": 5, "base_model": "Qwen/Qwen3-0.6B", "training_method": "LoRA", "epochs": 3, "status": "COMPLETED" }
  ],
  "training_jobs": [
    { "id": 8, "status": "COMPLETED", "progress": 100 }
  ],
  "models": [
    { "id": 2, "model_name": "hdfc_qwen3_0.6b_run_5", "version": "1.0.0", "base_model": "Qwen/Qwen3-0.6B", "status": "READY" }
  ],
  "evaluations": [
    { "evaluation_id": 3, "evaluation_status": "COMPLETED", "total_examples": 28, "answer_accuracy": 0.915 }
  ],
  "deployments": [
    { "id": 1, "version": "1.0.0", "environment": "development", "status": "ACTIVE", "endpoint": "http://localhost:8000/inference/predict" }
  ],
  "pipeline_stage": "DEPLOYED",
  "pipeline_complete": true
}
```

---

# 19. HTTP Status Code Reference

| Status Code | Meaning | Common Trigger Scenarios |
| :--- | :--- | :--- |
| **`200 OK`** | Request Successful | Standard GET, PUT, PATCH, and non-creation POST operations. |
| **`201 Created`** | Resource Created | User registration (`POST /auth/signup`). |
| **`400 Bad Request`** | Invalid Input / Business Rule Violation | Passwords do not match, unsupported file type, demoting only admin. |
| **`401 Unauthorized`** | Authentication Required / Invalid Token | Missing, invalid, or expired JWT Bearer token in header. |
| **`403 Forbidden`** | Insufficient Role Permissions / Deactivated User | User role does not satisfy `require_roles`, or account is deactivated. |
| **`404 Not Found`** | Resource Not Found | Dataset, Run, Job, Evaluation, Model, or Deployment ID does not exist. |
| **`422 Unprocessable Entity`** | Pydantic Validation Error | Missing required fields, out-of-range parameters (e.g. `epochs > 20`). |
| **`500 Internal Server Error`** | Unhandled Server Exception | Unexpected database or disk I/O errors. |
| **`503 Service Unavailable`** | Service / Hardware Failure | Database unreachable, CUDA Out Of Memory, Hugging Face timeout. |

---

# 20. Frontend Integration Guidelines

### 1. Axios Authorization Interceptor
Configure the frontend Axios client to automatically inject the JWT Bearer token and handle `401 Unauthorized` expiration:

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Dataset File Upload Handling
When uploading datasets, send a `multipart/form-data` payload:
```typescript
const formData = new FormData();
formData.append('datasetName', 'HDFC Branch Policy');
formData.append('category', 'Compliance');
formData.append('version', '1.0.0');
formData.append('source', 'Internal Audit');
formData.append('file', fileObject);

await apiClient.post('/datasets/upload-dataset', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});
```

### 3. Asynchronous Training & Evaluation Polling
For background operations (e.g., training runs and evaluation jobs):
1. Initiate the job via `POST /training/runs/{id}/start` or `POST /evaluations/{id}/start`.
2. Poll `GET /training/runs/{id}/detail` or `GET /training/runs/{id}/logs` every **3–5 seconds** until `status` becomes `"COMPLETED"`, `"FAILED"`, or `"STOPPED"`.

---

# 21. Complete API Endpoint Summary Table

| HTTP Method | Endpoint | Module | Auth Required | Allowed Roles | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | System | No | Public | Root API status & environment |
| `GET` | `/health` | System | No | Public | Health & database liveness probe |
| `POST` | `/auth/signup` | Auth | No | Public | Register new user account |
| `POST` | `/auth/login` | Auth | No | Public | Login & receive JWT access token |
| `GET` | `/auth/me` | Auth | **Yes** | All Users | Get current user profile |
| `POST` | `/auth/logout` | Auth | **Yes** | All Users | Logout current session |
| `GET` | `/auth/users` | Auth | **Yes** | `ADMIN` | List all platform users |
| `PUT` | `/auth/users/{user_id}/role` | Auth | **Yes** | `ADMIN` | Update user authorization role |
| `PATCH` | `/auth/users/{user_id}/status` | Auth | **Yes** | `ADMIN` | Activate / deactivate user account |
| `POST` | `/datasets/upload-dataset` | Datasets | **Yes** | `ADMIN`, `DS` | Upload new dataset file (multipart) |
| `GET` | `/datasets/` | Datasets | **Yes** | All Users | List all datasets & versions |
| `GET` | `/datasets/{dataset_id}` | Datasets | **Yes** | All Users | Get dataset by ID |
| `GET` | `/datasets/{dataset_id}/download` | Datasets | **Yes** | All Users | Download latest dataset file |
| `DELETE` | `/datasets/{dataset_id}` | Datasets | **Yes** | `ADMIN`, `DS` | Delete dataset by ID |
| `GET` | `/datasets/{dataset_id}/versions` | Datasets | No | Public | List version records of dataset |
| `GET` | `/datasets/versions/{version_id}/download` | Datasets | No | Public | Download specific dataset version |
| `POST` | `/data-processing/jobs` | Processing | **Yes** | `ADMIN`, `DS` | Start PII & data cleaning job |
| `GET` | `/data-processing/jobs/{job_id}` | Processing | **Yes** | All Users | Get processing job status |
| `GET` | `/data-processing/versions/{version_id}/metrics` | Processing | No | Public | Get dataset quality metrics |
| `POST` | `/training/runs` | Training | **Yes** | `ADMIN`, `DS` | Create training run config |
| `POST` | `/training/runs/{run_id}/start` | Training | **Yes** | `ADMIN`, `DS` | Start background training run |
| `POST` | `/training/runs/{run_id}/stop` | Training | **Yes** | `ADMIN`, `DS` | Stop running training run |
| `GET` | `/training/runs` | Training | **Yes** | All Users | List all training runs |
| `GET` | `/training/runs/{run_id}` | Training | **Yes** | All Users | Get training run summary |
| `GET` | `/training/runs/{run_id}/detail` | Training | No | Public | Get enriched training details & loss |
| `GET` | `/training/runs/{run_id}/logs` | Training | No | Public | Get real-time training step logs |
| `GET` | `/training-jobs` | Training Jobs | **Yes** | All Users | List worker training jobs |
| `GET` | `/training-jobs/{job_id}` | Training Jobs | **Yes** | All Users | Get worker training job by ID |
| `POST` | `/evaluations` | Evaluations | **Yes** | `ADMIN`, `DS`, `REVIEWER` | Create evaluation run |
| `GET` | `/evaluations/stats` | Evaluations | **Yes** | All Users | Get evaluation aggregate stats |
| `GET` | `/evaluations` | Evaluations | **Yes** | All Users | List evaluations (optional filter) |
| `GET` | `/evaluations/{evaluation_id}` | Evaluations | **Yes** | All Users | Get evaluation record by ID |
| `GET` | `/evaluations/{evaluation_id}/detail` | Evaluations | **Yes** | All Users | Get detailed benchmark breakdown |
| `POST` | `/evaluations/{evaluation_id}/start` | Evaluations | **Yes** | `ADMIN`, `DS`, `REVIEWER` | Start evaluation scoring job |
| `POST` | `/models` | Model Registry | **Yes** | `ADMIN`, `DS` | Register trained model / adapter |
| `GET` | `/models` | Model Registry | **Yes** | All Users | List registered models |
| `GET` | `/models/{model_id}` | Model Registry | No | Public | Get registered model by ID |
| `GET` | `/models/{model_id}/detail` | Model Registry | No | Public | Get 360-degree model details |
| `PATCH` | `/models/{model_id}/status` | Model Registry | **Yes** | `ADMIN`, `DS`, `REVIEWER` | Update model lifecycle status |
| `POST` | `/deployments` | Deployments | **Yes** | `ADMIN`, `DS` | Deploy model version |
| `GET` | `/deployments` | Deployments | **Yes** | All Users | List all deployments |
| `GET` | `/deployments/{deployment_id}` | Deployments | **Yes** | All Users | Get deployment by ID |
| `POST` | `/deployments/{deployment_id}/rollback` | Deployments | **Yes** | `ADMIN`, `DS` | Rollback to previous deployment |
| `POST` | `/deployments/{deployment_id}/undeploy` | Deployments | **Yes** | `ADMIN`, `DS` | Undeploy serving endpoint |
| `POST` | `/deployments/{deployment_id}/unload` | Deployments | **Yes** | `ADMIN`, `DS` | Unload model from memory |
| `POST` | `/deployments/{deployment_id}/reload` | Deployments | **Yes** | `ADMIN`, `DS` | Reload deployment |
| `POST` | `/deployments/{deployment_id}/restart` | Deployments | **Yes** | `ADMIN`, `DS` | Restart deployment instance |
| `POST` | `/deployments/{deployment_id}/start` | Deployments | **Yes** | `ADMIN`, `DS` | Start inactive deployment |
| `DELETE` | `/deployments/{deployment_id}` | Deployments | **Yes** | `ADMIN`, `DS` | Delete deployment record |
| `POST` | `/inference/predict` | Inference | **Yes** | All Users | Predict using registered model |
| `GET` | `/inference/models` | Inference | **Yes** | All Users | List loaded runtime models |
| `POST` | `/inference/unload` | Inference | **Yes** | `ADMIN`, `DS` | Unload inference adapter from RAM |
| `POST` | `/ai/generate` | AI Direct | No | Public | Direct inference by model key |
| `GET` | `/pipeline/dashboard/stats` | Pipeline | **Yes** | All Users | Get live aggregate dashboard stats |
| `GET` | `/pipeline/status/{dataset_version_id}` | Pipeline | **Yes** | All Users | Get end-to-end version lineage |
