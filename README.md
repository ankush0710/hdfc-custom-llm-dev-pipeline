# HDFC Custom LLM Development Pipeline

An end-to-end development pipeline for building, evaluating, and integrating a banking-domain Large Language Model (LLM) system with a data-engineering layer, AI/ML layer, FastAPI backend, frontend, evaluation workflows, and MLOps documentation.

> **Project status:** Final integration and submission hardening in progress.

---

## 1. Project Overview

This project develops a banking-domain custom LLM pipeline for HDFC-oriented customer-service and banking use cases.

The system brings together:

- curated and validated banking datasets
- dataset preparation, validation, lineage, and release management
- LoRA-based fine-tuning of a compact language model
- a model registry and multi-model inference layer
- FastAPI backend integration
- frontend integration
- structured evaluation and QA
- MLOps/MLflow tracking and technical documentation

The architecture is intentionally modular so that data engineering, model training, inference, backend integration, evaluation, and documentation can be developed and verified independently.

---

## 2. Project Goals

The project aims to:

1. Prepare a reliable banking-domain dataset suitable for model development.
2. Fine-tune a compact open-weight model using LoRA.
3. Provide a common inference boundary for multiple models.
4. Connect the AI layer to the application backend and frontend.
5. Evaluate model behavior across intent classification, grounded generation, FAQ/domain QA, and robustness/security scenarios.
6. Preserve dataset/model lineage and reproducibility information.
7. Produce a submission-ready technical and MLOps record.

---

## 3. High-Level Architecture

```text
                         DATA LAYER
                              |
                              v
                 Dataset Preparation & QA
                              |
                              v
                    Versioned Data Release
                              |
                              v
                       AI / ML LAYER
        +---------------------------------------------+
        | Model Registry                              |
        |                                             |
        | Qwen3-0.6B + HDFC LoRA     <-- primary     |
        | Qwen2.5-1.5B-Instruct      <-- baseline    |
        | SmolLM2-1.7B-Instruct      <-- baseline    |
        +---------------------------------------------+
                              |
                              v
                    AI Inference Service
                              |
                              v
                           FastAPI
                              |
                              v
                         Frontend UI
```

Supporting layers:

```text
Evaluation / QA  <---->  AI layer
MLOps / MLflow   <---->  Training + Evaluation
Documentation    <---->  Entire pipeline
```

---

## 4. Repository Structure

```text
hdfc-custom-llm-dev-pipeline/
│
├── ai/                         # AI/ML implementation
│   ├── artifacts/              # Final model artifacts
│   ├── config/                 # Model/config registry
│   ├── evaluation/             # Evaluation implementation
│   ├── inference/              # Inference service and generators
│   ├── models/                 # Model registry implementation
│   ├── model_selection/        # Model selection documentation
│   ├── tests/                  # AI test suite
│   ├── training/               # Training and LoRA implementation
│   └── utils/                  # Hardware/utilities
│
├── backend/                    # FastAPI + database backend
├── frontend/                   # Application frontend
│
├── data/                       # Official repository data artifacts
├── manifests/                  # Dataset release manifests/hashes
├── schema/                     # Dataset schemas
│
├── docs/
│   ├── api/                    # API documentation
│   ├── architecture/           # System/ML/backend/frontend architecture
│   ├── data-engineering/       # Dataset engineering documentation
│   ├── frontend/               # Frontend documentation
│   └── requirements/           # Project requirements
│
└── README.md
```

---

## 5. AI / ML Layer

### Supported models

The model registry currently defines these enabled models:

| Model ID | Model | Parameters | Purpose |
|---|---|---:|---|
| `qwen2_5_1_5b_instruct` | Qwen/Qwen2.5-1.5B-Instruct | 1.54B | Instruction-generation baseline |
| `qwen3_0_6b` | Qwen/Qwen3-0.6B | 0.6B | Primary HDFC fine-tuned model |
| `smollm2_1_7b_instruct` | HuggingFaceTB/SmolLM2-1.7B-Instruct | 1.7B | Instruction-generation baseline |

All three models are enabled in the model registry and marked for local testing.

### Fine-tuned HDFC model

The primary custom model is based on:

```text
Qwen/Qwen3-0.6B
```

with a LoRA adapter stored under:

```text
ai/artifacts/full_training/
```

The model artifact is a PEFT/LoRA fine-tuned adapter intended for text-generation inference.

---

## 6. AI Inference Architecture

The AI layer exposes a reusable inference boundary so that the application backend does not need to duplicate model-loading logic.

The main responsibilities of the AI layer are:

- model lookup and selection
- model loading
- fine-tuned adapter loading
- text generation
- structured response handling
- baseline vs fine-tuned inference
- evaluation support
- hardware/runtime checks

The backend should integrate through the existing inference/service boundary.

---

## 7. Dataset Lineage

Two important dataset releases must remain clearly distinguished.

### Release A — current Qwen3 training/evaluation lineage

The current Qwen3 HDFC LoRA model was trained/evaluated against:

| Split | Records |
|---|---:|
| Train | 19,476 |
| Validation | 2,434 |
| Test | 2,436 |
| **Total** | **24,346** |

### Release B — expanded frozen master release

The newer finalized release is:

```text
v2.0.0-expanded
```

| Split | Records |
|---|---:|
| Train | 47,476 |
| Validation | 5,934 |
| Test | 5,936 |
| **Total** | **59,346** |

**Important:** Release B is the newer frozen master dataset and was **not** used to retrain the current Qwen3 model.

The dataset-engineering release also records duplicate-ID, cross-split overlap, invalid-JSON, missing-field, and PII checks as part of the release-quality process.

---

## 8. Data Engineering

The data-engineering layer provides:

- dataset preparation
- validation
- split-integrity verification
- schema definition
- dataset/model lineage
- release history
- release manifests
- SHA-256 hashes
- reproducibility scripts
- frozen QA test data

Related documentation is available under:

```text
docs/data-engineering/
```

and release metadata is under:

```text
manifests/
schema/
```

---

## 9. Backend and Frontend

The application layer consists of:

```text
Frontend
   |
   v
FastAPI backend
   |
   +--> application routes/services
   |
   +--> database layer
   |
   +--> AI inference integration
```

The backend includes database migrations through Alembic and uses PostgreSQL for local development.

The exact API request/response contract should be maintained in:

```text
docs/api/
```

and verified against the current FastAPI Swagger/OpenAPI output.

---

## 10. Evaluation and QA

### AI test suite

The repository AI test suite has been verified locally with:

```text
43 passed
3 skipped
0 failed
```

The three skips are integration-marked tests; they are not failed tests.

### Member 4 QA suite

The final GPU QA execution covered:

```text
28 total tests
28 completed
0 runtime errors
27 automated PASS
1 automated FAIL
Average latency: 12.606 seconds
```

The models exercised were:

- Qwen3-0.6B + HDFC LoRA
- Qwen2.5-1.5B-Instruct
- SmolLM2-1.7B-Instruct

### Known QA finding

The one automated failure was:

```text
SFT-006
```

The Qwen3 model generated:

```text
HDFC Master Policy Doc #436
```

as a citation even though that citation was not present in the supplied QA fixture context.

This is recorded as a groundedness/citation-integrity issue and should remain visible in the final QA report. It should not be hidden by changing the test.

Human semantic review is required for final QA sign-off.

---

## 11. MLOps / MLflow

MLflow is used as the MLOps tracking layer for experiment metadata, metrics, and artifacts.

Where the original training run was not live-tracked by MLflow, any reconstruction must be explicitly identified as a:

```text
retrospective tracking run
```

and must not be presented as live historical tracking.

Recommended tracked items include:

- base model
- LoRA configuration
- dataset release
- training parameters
- evaluation metrics
- final model/adapter artifact
- QA summary
- reproducibility metadata
- source Git commit

---

## 12. Local AI Environment

The verified AI development environment used for local GPU testing is based on:

```text
Python 3.11.9
NVIDIA GeForce GTX 1650 Ti
4 GB VRAM
CUDA-enabled PyTorch
```

AI environment validation:

```powershell
python -m pytest ai/tests -q
pip check
```

Expected verification:

```text
43 passed, 3 skipped, 0 failed
No broken requirements found.
```

Keep the AI environment separate from the backend-specific virtual environment.

---

## 13. Backend Local Development

The backend uses a separate Python virtual environment under:

```text
backend/.venv/
```

Local development uses PostgreSQL.

The backend expects a local:

```text
backend/.env
```

with:

```env
DATABASE_URL=postgresql://postgres:<YOUR_PASSWORD>@localhost:5432/hdfc_llm_custom_pipeline
```

**Never commit `.env` or real database credentials.**

The backend should be started only after the local database configuration and migrations are working.

---

## 14. Development Workflow

### AI tests

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest ai/tests -q
```

### Backend

From:

```text
backend/
```

activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

then configure the local `.env`, run migrations, and start FastAPI:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger/OpenAPI is available at:

```text
http://127.0.0.1:8000/docs
```

Use the current repository API documentation and Swagger schema for the authoritative endpoint details.

---

## 15. Security and Configuration

Never commit:

```text
.env
backend/.env
virtual environments
private credentials
database passwords
temporary secrets
```

Raw/full datasets and large training artifacts should only be committed when intentionally required by the repository release policy.

---

## 16. Team Responsibilities

| Member | Role | Primary Ownership |
|---|---|---|
| Member 1 | AI Lead | Model Training & Integration |
| Member 2 | Data Engineer | Dataset Preparation |
| Member 3 | Full Stack + DevOps | Frontend, Backend, Deployment |
| Member 4 | AI Evaluation Engineer | Prompt Engineering, Model Testing |
| Member 5 | MLOps Engineer | MLflow, experiment tracking, MLOps support |
| Member 6 | Documentation Lead | Project documentation, technical reports, final documentation consolidation |

---

## 17. Current Project Status

### Completed

- AI model training/integration
- Qwen3 LoRA adapter
- model registry
- multi-model inference infrastructure
- AI test framework
- dataset engineering release
- dataset schemas/manifests/hashes
- Member 4 GPU QA execution
- primary repository integration work

### Finalization items

- backend migration/API final verification
- frontend-to-backend-to-AI end-to-end verification
- Member 4 human semantic QA sign-off
- retrospective MLflow run
- final documentation consolidation
- final repository cleanup and freeze

---

## 18. Final Submission Checklist

Before submission, verify:

- [ ] `main` contains all approved team work
- [ ] AI test suite passes
- [ ] backend database migration succeeds
- [ ] FastAPI starts successfully
- [ ] Swagger/OpenAPI loads
- [ ] inference endpoint works
- [ ] frontend-to-backend-to-AI flow works
- [ ] Member 4 final QA report is complete
- [ ] SFT-006 limitation is documented
- [ ] MLflow/MLOps documentation is complete
- [ ] README and architecture documentation match the actual implementation
- [ ] dataset lineage numbers are consistent everywhere
- [ ] no `.env` or secrets are committed
- [ ] no virtual environments or temporary files are committed
- [ ] final repository status is clean

---

## 19. Documentation Map

| Topic | Location |
|---|---|
| Project overview | `README.md` |
| System architecture | `docs/architecture/system-architecture.md` |
| ML architecture | `docs/architecture/ml-architecture.md` |
| Backend architecture | `docs/architecture/backend-architecture.md` |
| Frontend architecture | `docs/architecture/frontend-architecture.md` |
| API documentation | `docs/api/` |
| Data engineering | `docs/data-engineering/` |
| Dataset schemas | `schema/` |
| Dataset release manifests | `manifests/` |
| AI implementation | `ai/` |
| AI tests | `ai/tests/` |
| Model artifact | `ai/artifacts/full_training/` |

---

## 20. Final Note

The repository should be treated as a reproducible engineering project rather than only as a model-training submission.

The final state should allow a reviewer to trace:

```text
Dataset
  -> Data validation
  -> Dataset release
  -> Model training
  -> LoRA adapter
  -> Model registry
  -> Inference service
  -> Backend API
  -> Frontend
  -> Evaluation / QA
  -> MLOps / Documentation
```

That traceability is the central goal of the development pipeline.
