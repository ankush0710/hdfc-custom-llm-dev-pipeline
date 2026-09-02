# HDFC Custom LLM Development Pipeline: Project Requirements Specification

> **Document Type:** Production Requirements Specification Document (PRD)  
> **Version:** 2.0.0 (Synchronized with Actual Production Architecture)  
> **Project:** HDFC Bank Custom LLM Development Pipeline (`hdfc-custom-llm-dev-pipeline`)  
> **Status:** Fully Aligned with Implementation  
> **Target Frameworks:** Next.js 16.3.0 (App Router) / FastAPI 0.141.1 / Neon PostgreSQL / PyTorch & PEFT  

---

## 📌 Table of Contents

1. [Executive Summary & Document Scope](#1-executive-summary--document-scope)
2. [Technology Stack & Platform Architecture](#2-technology-stack--platform-architecture)
3. [System Architecture & Projectional Model](#3-system-architecture--projectional-model)
4. [Multi-Dimensional Module Requirements](#4-multi-dimensional-module-requirements)
   * [Module 1: Authentication & Role-Based Access Control (RBAC)](#module-1-authentication--role-based-access-control-rbac)
   * [Module 2: Dataset Management & Multi-Format Ingestion](#module-2-dataset-management--multi-format-ingestion)
   * [Module 3: Data Quality Processing & PII De-Identification](#module-3-data-quality-processing--pii-de-identification)
   * [Module 4: Supervised Fine-Tuning (SFT / LoRA) & Live Training Telemetry](#module-4-supervised-fine-tuning-sft--lora--live-training-telemetry)
   * [Module 5: Automated Benchmark Evaluation & Safety Guardrails](#module-5-automated-benchmark-evaluation--safety-guardrails)
   * [Module 6: Model Registry & 360° Lineage Management](#module-6-model-registry--360-lineage-management)
   * [Module 7: Model Deployment & Quality Gate Serving](#module-7-model-deployment--quality-gate-serving)
   * [Module 8: Interactive AI Playground & Multi-Turn Inference](#module-8-interactive-ai-playground--multi-turn-inference)
   * [Module 9: Executive Dashboard & Pipeline Lineage Tracking](#module-9-executive-dashboard--pipeline-lineage-tracking)
5. [Non-Functional Requirements & Enterprise SLAs](#5-non-functional-requirements--enterprise-slas)
6. [Directory Structure & Implementation Mapping](#6-directory-structure--implementation-mapping)
7. [Verification & Acceptance Criteria](#7-verification--acceptance-criteria)

---

# 1. Executive Summary & Document Scope

The **HDFC Bank Custom LLM Development Pipeline** is an enterprise MLOps governance platform purpose-built for the banking sector. It manages the entire lifecycle of proprietary, domain-specialized Large Language Models:

1. **Governed Data Ingestion:** Uploading banking datasets, versioning, PII detection/sanitization, and Hugging Face Hub synchronization.
2. **LoRA Fine-Tuning Orchestration:** Fine-tuning foundation models (`Qwen/Qwen2.5-1.5B-Instruct`, `Qwen/Qwen3-0.6B`, `HuggingFaceTB/SmolLM2-1.7B-Instruct`) with live step-level loss and learning rate telemetry streaming.
3. **Rigorous Quality Gate Benchmarking:** Automated multi-dimensional evaluation (intent classification, structured response accuracy, citation fidelity, escalation detection, and safety violation checks).
4. **Governed Deployment & Inference:** Quality-gated deployment lifecycle (Rollback, Reload, Restart) and real-time inference playground with banking policy context.
5. **Enterprise Security:** JWT-based stateless authentication, bcrypt password hashing, and granular 4-tier Role-Based Access Control (`ADMIN`, `DS`, `REVIEWER`, `VIEWER`).

---

# 2. Technology Stack & Platform Architecture

### 2.1 Core Stack Breakdown

```text
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND LAYER                                     │
│  [ Next.js 16.3.0 (App Router) ]  [ React 19.2.8 ]  [ Tailwind CSS v4 ]               │
│  [ Lucide React Icons ]           [ Recharts 3.10 ]  [ Axios 1.19.0 ]  [ Sonner ]     │
└──────────────────────────────────────────┬────────────────────────────────────────────┘
                                           │ HTTP / REST (JWT Bearer Auth)
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                    BACKEND LAYER                                      │
│  [ FastAPI 0.141.1 ]  [ Pydantic v2 ]  [ PyTorch 2.13 ]  [ PEFT 0.20 ]  [ Uvicorn ]   │
│  [ Hugging Face Hub SDK ]  [ PyJWT + Bcrypt ]  [ BackgroundTasks & Threads ]          │
└──────────────────────────────────────────┬────────────────────────────────────────────┘
                                           │ SQLAlchemy 2.0 (Psycopg2 Pool)
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                     DATA LAYER                                        │
│  [ Neon Serverless PostgreSQL 16 ]  [ Local Cache Storage ]  [ Hugging Face Repos ]   │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

| Domain / Layer | Technology | Actual Version | Core Responsibilities & Capabilities |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | **Next.js** | `16.3.0` | App Router routing, dynamic routes (`[id]`), SSR shell, asset optimization. |
| **UI Library** | **React / React DOM**| `19.2.8` | Declarative UI rendering, hooks lifecycle (`useState`, `useEffect`, `useCallback`). |
| **Styling & Theme** | **Tailwind CSS** | `^4.0.0` | Utility-first styling, Merriweather Serif font variable, HDFC brand color tokens. |
| **Data Fetching** | **Axios** | `^1.19.0` | Centralized `apiClient.js`, Bearer JWT injection, multipart form-data boundary handling. |
| **Data Visualization**| **Recharts** | `^3.10.1` | Step-level training loss sparklines, evaluation metric radars, and throughput bars. |
| **Iconography** | **Lucide React** | `^1.30.0` | Vector icons for navigation, status badges, and interactive controls. |
| **Notifications** | **Sonner** | `^2.0.8` | Rich toast notifications for API success, error handling, and permission alerts. |
| **Backend API** | **FastAPI** | `0.141.1` | Asynchronous REST routing, OpenAPI 3.1 documentation, dependency injection. |
| **Data Validation** | **Pydantic** | `^2.13.4` | Strict request parsing, coercion, schema validation, and error serialization. |
| **AI / ML Runtime** | **PyTorch / PEFT** | `^2.13.0` / `^0.20.0`| SFT LoRA fine-tuning, tokenizer chat templating, model inference execution. |
| **Database Engine** | **Neon PostgreSQL** | PostgreSQL 16 | Relational persistence for datasets, runs, evaluations, models, deployments, users. |
| **ORM & Migrations**| **SQLAlchemy / Alembic**| `^2.0.52` / `^1.19.1`| Declarative database mapping, connection pooling, and migration tracking. |

---

# 3. System Architecture & Projectional Model

```mermaid
graph TD
    subgraph Client ["Frontend View Projection (Next.js 16 + React 19)"]
        UI["Next.js App Router Pages"]
        AuthCtx["AuthContext & RBAC Guard"]
        AxiosClient["apiClient.js (Axios)"]
        Charts["Recharts Visualizations"]
    end

    subgraph Server ["Backend Service Projection (FastAPI)"]
        Router["FastAPI Routers (11 Modules)"]
        AuthDep["auth_dependency.py (JWT + RBAC)"]
        Services["Domain Business Services"]
        AIAdapters["AI Training & Inference Adapters"]
    end

    subgraph Storage ["Data Persistence Projection (Neon PostgreSQL & HF Hub)"]
        DB[("Neon Managed PostgreSQL")]
        HFHub["☁️ Hugging Face Hub (Datasets & Models)"]
        Disk["Local File Storage (uploads/ & cache)"]
    end

    UI --> AuthCtx
    AuthCtx --> AxiosClient
    Charts --> AxiosClient
    AxiosClient -->|REST API Requests (Bearer Token)| Router
    Router --> AuthDep
    AuthDep --> Services
    Services --> AIAdapters
    Services --> DB
    Services --> Disk
    Services --> HFHub
```

---

# 4. Multi-Dimensional Module Requirements

---

### Module 1: Authentication & Role-Based Access Control (RBAC)

#### Description
Stateless JWT Bearer token authentication with bcrypt password hashing and 4-tier Role-Based Access Control (`ADMIN`, `DS`, `REVIEWER`, `VIEWER`).

* **Frontend View:** `/login`, `/signup`, `/admin/users` (Protected with `allowedRoles={["ADMIN"]}`).
* **UI Components:** `src/components/auth/ProtectedRoute.jsx`, `src/components/layout/Navbar.jsx` (Role Badge), `Sidebar.jsx` (Admin Menu Filter).
* **API Endpoints:**
  * `POST /auth/signup` (201 Created)
  * `POST /auth/login` (200 OK — Returns `access_token` and user object)
  * `GET /auth/me` (200 OK — Returns current user profile)
  * `POST /auth/logout` (200 OK)
  * `GET /auth/users` (200 OK — `ADMIN` only)
  * `PUT /auth/users/{user_id}/role` (200 OK — `ADMIN` only)
  * `PATCH /auth/users/{user_id}/status` (200 OK — `ADMIN` only)
* **Database Entity (`users` table):**
  * `id` (PK Integer), `full_name` (String), `email` (Unique String), `password_hash` (String), `role` (String), `is_active` (Boolean), `created_at`, `updated_at`.

---

### Module 2: Dataset Management & Multi-Format Ingestion

#### Description
Ingest multi-format banking datasets (`.csv`, `.xlsx`, `.json`, `.jsonl`), create immutable dataset versions, and synchronize automatically with Hugging Face Hub (`HF_DATASET_REPO`).

* **Frontend View:** `/dataset`, `/dataset/uploadDataset`, `/dataset/[id]`.
* **UI Components:** `FileUpload.jsx`, `DatasetTableColumns`, `Breadcrumbs.jsx`, `StatCard.jsx`.
* **API Endpoints:**
  * `POST /datasets/upload-dataset` (Multipart Form Upload)
  * `GET /datasets` (List all datasets & versions)
  * `GET /datasets/{dataset_id}` (Get dataset by ID)
  * `GET /datasets/{dataset_id}/download` (Stream/download dataset file)
  * `DELETE /datasets/{dataset_id}` (Delete dataset & versions)
  * `GET /datasets/{dataset_id}/versions` (List versions of dataset)
  * `GET /datasets/versions/{version_id}/download` (Download specific version)
* **Database Entities:** `dataset` (Parent) and `dataset_version` (Version child with `file_hash`, `huggingface_repo`, `huggingface_path`, `commit_hash`, `is_safe_for_training`).

---

### Module 3: Data Quality Processing & PII De-Identification

#### Description
Pre-training data sanitization pipeline. Scans sensitive banking entities (Account Numbers, Credit Cards, Phone Numbers, PAN, Aadhaar), de-identifies PII, removes duplicate rows, and computes quality scores.

* **Frontend View:** Embedded inside `/dataset/[id]`.
* **UI Components:** `QualityMetrics.jsx`, PII instance tags, `is_safe_for_training` status badge.
* **API Endpoints:**
  * `POST /data-processing/jobs` (Trigger PII & cleaning pipeline)
  * `GET /data-processing/jobs/{job_id}` (Get job execution status)
  * `GET /data-processing/versions/{version_id}/metrics` (Get statistical metrics & quality score)
* **Database Entities:** `processing_job` (Job run) and `quality_metrics` (Stores `total_rows`, `duplicate_rows`, `quality_score`, `pii_instances_detected`, `pii_types_detected`, `records_sanitized`, `is_safe_for_training`).

---

### Module 4: Supervised Fine-Tuning (SFT / LoRA) & Live Training Telemetry

#### Description
Orchestrates Parameter-Efficient Fine-Tuning (PEFT / LoRA) on validated foundation models. Persists step-level loss, learning rate, and progress to PostgreSQL, and uploads fine-tuned LoRA adapters to Hugging Face Hub (`HF_MODEL_REPO`).

* **Supported Base Models:** `qwen2_5_1_5b_instruct`, `qwen3_0_6b`, `smollm2_1_7b_instruct`.
* **Frontend View:** `/training`, `/training/[id]` (Live step-level training loss telemetry dashboard).
* **UI Components:** `NewTrainingModal.jsx`, `LineChart.jsx`, `TrainingJobStats.jsx`, real-time progress bar.
* **API Endpoints:**
  * `POST /training/runs` (Create training run configuration)
  * `POST /training/runs/{run_id}/start` (Launch background training worker)
  * `POST /training/runs/{run_id}/stop` (Graceful thread-safe cancellation)
  * `GET /training/runs` (List all runs)
  * `GET /training/runs/{run_id}` (Get run summary)
  * `GET /training/runs/{run_id}/detail` (Get enriched training metrics & step loss history)
  * `GET /training/runs/{run_id}/logs` (Get formatted training logs)
  * `GET /training-jobs` & `GET /training-jobs/{job_id}` (Worker job queries)
* **Database Entities:** `training_run` and `training_job` (Stores `train_loss`, `current_lr`, `current_step`, `max_steps`, `log_entries` JSON array).

---

### Module 5: Automated Benchmark Evaluation & Safety Guardrails

#### Description
Scores fine-tuned models against benchmark test fixtures across intent classification, structured answer fidelity, citation accuracy, policy escalation, and critical safety violations (e.g. phishing link clicks).

* **Frontend View:** `/evaluation`, `/evaluation/[id]`.
* **UI Components:** `NewEvaluationModal.jsx`, `EvaluationMetricsGrid.jsx`, `EvaluationOverallScoreCard.jsx`, `EvaluationBenchmarkBreakdownCard.jsx`.
* **API Endpoints:**
  * `POST /evaluations` (Create & auto-start benchmark scoring)
  * `GET /evaluations/stats` (Aggregate evaluation statistics)
  * `GET /evaluations` (List evaluation runs)
  * `GET /evaluations/{evaluation_id}` (Get evaluation summary)
  * `GET /evaluations/{evaluation_id}/detail` (Get detailed multi-metric breakdown)
  * `POST /evaluations/{evaluation_id}/start` (Manual start trigger)
* **Database Entity (`evaluation` table):** Stores `intent_json_validity`, `intent_structured_accuracy`, `answer_accuracy`, `citation_accuracy`, `policy_flag_accuracy`, `escalation_accuracy`, `critical_safety_failures`, `infrastructure_errors`, `average_latency_seconds`.

---

### Module 6: Model Registry & 360° Lineage Management

#### Description
Central catalog and governance gatekeeper for fine-tuned LoRA adapters and model checkpoints. Enforces lifecycle status states (`CREATED`, `READY`, `ACTIVE`, `ARCHIVED`).

* **Frontend View:** `/model`, `/model/[id]`.
* **UI Components:** `ModelsTable.jsx`, `ModelDetailsDrawer.jsx`, `ModelOverviewCard.jsx`, `ModelPerformanceMetricsCard.jsx`, `ModelLogsModal.jsx`.
* **API Endpoints:**
  * `POST /models` (Register model / LoRA adapter)
  * `GET /models` (List all registered models)
  * `GET /models/{model_id}` (Get model by ID)
  * `GET /models/{model_id}/detail` (Get 360° model card with dataset lineage and loss history)
  * `PATCH /models/{model_id}/status` (Update lifecycle status)
* **Database Entity (`model_registry` table):** Stores `model_name`, `version`, `base_model`, `artifact_path`, `adapter_path`, `huggingface_repo`, `huggingface_path`, `commit_hash`, `model_size`, `training_job_id`, `evaluation_id`, `status`.

---

### Module 7: Model Deployment & Quality Gate Serving

#### Description
Manages model serving endpoints across `development`, `staging`, and `production`. Validates that models satisfy the Quality Gate policy before permitting deployment.

* **Quality Gate Policy:** Enforces `VALID_DEPLOYABLE_STATUSES = {"READY", "APPROVED", "DEPLOYED"}`. Blocks `REJECTED` or `FAILED` models.
* **Frontend View:** `/deployment`, `/deployment/[id]`.
* **UI Components:** `DeployNewModelModal.jsx`, `DeploymentOverviewCard.jsx`, `DeploymentAdminActionsCard.jsx`, `DeploymentHealthMetricsCard.jsx`.
* **API Endpoints:**
  * `POST /deployments` (Deploy model to target environment)
  * `GET /deployments` (List deployments)
  * `GET /deployments/{deployment_id}` (Get deployment details)
  * `POST /deployments/{deployment_id}/rollback` (Rollback to previous stable version)
  * `POST /deployments/{deployment_id}/undeploy` (Deactivate endpoint)
  * `POST /deployments/{deployment_id}/reload` (Reload model weights)
  * `POST /deployments/{deployment_id}/restart` (Restart serving instance)
  * `DELETE /deployments/{deployment_id}` (Delete deployment record)
* **Database Entity (`deployment` table):** Stores `model_id`, `version`, `environment`, `status`, `endpoint`.

---

### Module 8: Interactive AI Playground & Multi-Turn Inference

#### Description
Interactive chat sandbox targeting deployed fine-tuned model endpoints with prompt template formatting, context injection, and hyperparameter controls.

* **Frontend View:** `/playground`.
* **UI Components:** `PlaygroundChatWindow.jsx`, `PlaygroundParametersPanel.jsx` (Sliders for `temperature`, `top_p`, `max_tokens`, and system role persona selection).
* **API Endpoints:**
  * `POST /inference/predict` (Predict using database-registered model ID)
  * `GET /inference/models` (List loaded models in memory)
  * `POST /inference/unload` (Free GPU memory)
  * `POST /ai/generate` (Direct inference via model key)

---

### Module 9: Executive Dashboard & Pipeline Lineage Tracking

#### Description
Central monitoring hub providing live aggregate statistics, active deployment tables, recent activity timeline, and end-to-end dataset lineage snapshots.

* **Frontend View:** `/` (Main Dashboard).
* **UI Components:** `StatCard.jsx`, `LineChart.jsx`, `ModelsTable.jsx`, `ActivityCard.jsx`.
* **API Endpoints:**
  * `GET /pipeline/dashboard/stats` (Live aggregate counts & recent activity feed)
  * `GET /pipeline/status/{dataset_version_id}` (Full version lineage snapshot: `dataset -> processing -> training -> model -> evaluation -> deployment`)

---

# 5. Non-Functional Requirements & Enterprise SLAs

### 5.1 Performance & Latency
* **Frontend Responsiveness:** First Contentful Paint (FCP) `< 1.2s`, Time to Interactive (TTI) `< 1.8s`.
* **Telemetry Streaming:** Training step loss and progress polling interval set to **3–5 seconds** with low overhead.
* **Database Operations:** P95 response time `< 25ms` for indexed queries using connection pooling (`pool_size=5`, `max_overflow=10`, `pool_recycle=300`).

### 5.2 Enterprise Security & Compliance
* **Data Privacy:** Raw datasets cannot be used for model training until PII scanning and de-identification is completed (`is_safe_for_training=True`).
* **Authentication:** Stateless HMAC-SHA256 JWT tokens with 24-hour expiration (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440`).
* **Password Hashing:** Passwords hashed with `bcrypt` using salted one-way derivation.
* **CORS Governance:** Explicit whitelisting of trusted origins (`http://localhost:3000`, `ALLOW_ORIGIN`).

---

# 6. Directory Structure & Implementation Mapping

```text
hdfc-custom-llm-dev-pipeline/
├── frontend/                        # Next.js 16 App Router Application
│   ├── src/
│   │   ├── app/                     # Page Routes (/, /dataset, /training, /evaluation, /model, /deployment, /playground, /admin)
│   │   │   ├── context/             # AuthContext.jsx
│   │   │   ├── services/            # apiClient.js & Domain Service Modules
│   │   │   ├── globals.css          # Tailwind CSS v4 directives
│   │   │   └── layout.js            # Root layout shell
│   │   └── components/              # UI Primitives, Modals, Forms, Tables, Charts
│   └── package.json                 # Dependencies (next, react, tailwindcss, recharts, axios, sonner, lucide-react)
│
├── backend/                         # FastAPI Backend Service
│   ├── app/
│   │   ├── main.py                  # App entrypoint, CORS, Seed Admin, Router inclusion
│   │   ├── core/                    # auth_dependency.py, config.py
│   │   ├── dbConfig/                # database_config.py (Neon SQLAlchemy engine)
│   │   ├── model/                   # 11 Declarative ORM entities
│   │   ├── processor/               # PII detector, cleaner, quality calculator
│   │   ├── routes/                  # 11 Domain API routers
│   │   ├── schema/                  # Pydantic v2 validation schemas
│   │   ├── services/                # Business domain services & HF storage
│   │   └── ai/                      # AI training, evaluation & inference adapters
│   └── requirements.txt             # Backend dependencies
│
├── docs/                            # Project Documentation
│   ├── api_contract/                # API_CONTRACT.md
│   ├── backend_architecture/        # BACKEND_ARCHITECTURE.md
│   ├── frontend_architecture/       # FRONTEND_ARCHITECTURE.md, COMPONENT_GUIDELINES.md, UI_GUIDELINES.md
│   └── requirements/                # project_requirements.md [THIS SPECIFICATION]
└── README.md                        # Master Project Documentation
```

---

# 7. Verification & Acceptance Criteria

1. **Authentication & RBAC Integrity:** All protected routes require a valid JWT Bearer token; privileged admin endpoints reject non-admin users with `403 Forbidden`.
2. **Dataset Safety Guard:** Training runs reject un-sanitized raw datasets with `400 Bad Request` until PII cleaning is completed.
3. **Training & Hub Push:** Completed training runs successfully persist step telemetry and push `.safetensors` LoRA adapters to Hugging Face Hub (`ankush0710/hdfc-llm-models`).
4. **Quality Gate Verification:** Models with `REJECTED` or `FAILED` evaluation scores cannot be deployed to active endpoints.
5. **Real-Time UI Telemetry:** Training loss curves and evaluation benchmarks render dynamically using Recharts without UI freezing.
