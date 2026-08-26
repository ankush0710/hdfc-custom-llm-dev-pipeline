# System Architecture

## 1. Overview

The HDFC Custom LLM development pipeline is organized into five major layers:

1. Data Engineering
2. AI / ML
3. Backend
4. Frontend
5. Evaluation / MLOps / Documentation

The architecture is modular so that each layer can be developed and verified independently while supporting an integrated application flow.

## 2. High-Level Architecture

```text
                     DATA ENGINEERING
                            |
                            v
                 Dataset Preparation
                            |
                            v
                  Validation / QA
                            |
                            v
                   Versioned Release
                            |
                            v
                         AI / ML
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
      Model Registry    Fine-Tuning      Evaluation
          |
          v
   Inference Service
          |
          v
       FASTAPI
          |
     +----+----+
     |         |
     v         v
 Database    Application
 PostgreSQL   Services
     |
     v
   FRONTEND
     |
     v
   End User
```

Evaluation, MLOps, and documentation operate across the relevant layers.

## 3. Data Engineering Layer

Responsibilities include:

- source dataset preparation
- validation
- schema enforcement
- split integrity
- dataset lineage
- release versioning
- release manifests
- SHA-256 hashes
- reproducibility artifacts

Primary locations:

```text
data/
manifests/
schema/
docs/data-engineering/
```

## 4. AI / ML Layer

The AI layer contains:

```text
ai/
├── config/
├── models/
├── inference/
├── training/
├── evaluation/
├── tests/
└── artifacts/
```

Its responsibilities include:

- model registry
- model selection
- LoRA training
- model loading
- inference
- structured responses
- evaluation
- hardware/runtime verification

The primary fine-tuned model is:

```text
Qwen/Qwen3-0.6B + HDFC LoRA
```

Baseline models:

```text
Qwen/Qwen2.5-1.5B-Instruct
SmolLM2-1.7B-Instruct
```

## 5. Backend Layer

The backend is implemented using FastAPI and provides the application/API layer.

Major responsibilities include:

- API routing
- application services
- database access
- dataset/model-related application workflows
- AI integration
- request/response handling

Relevant location:

```text
backend/
```

The backend should use the existing AI inference/service boundary rather than duplicating model-loading logic.

## 6. Database Layer

Local development uses PostgreSQL.

The development connection is configured through:

```text
backend/.env
```

using `DATABASE_URL`.

Database migrations are maintained through:

```text
backend/alembic/
```

Credentials must remain local and must never be committed.

## 7. Frontend Layer

The frontend provides the user-facing application interface.

High-level flow:

```text
User
 |
 v
Frontend UI
 |
 v
Backend API
 |
 v
Application Services
 |
 +----> AI
 |
 +----> Database
 |
 v
Response
 |
 v
Frontend UI
```

The exact frontend page structure and API contract should remain documented in the corresponding frontend/API documentation.

## 8. AI Integration Boundary

The AI integration is intentionally separated from the backend:

```text
Backend
   |
   v
AI Inference Boundary
   |
   v
Model Registry
   |
   +----> Qwen3 + LoRA
   |
   +----> Qwen2.5
   |
   +----> SmolLM2
```

This keeps model loading, adapter handling, model selection, and generation inside the AI layer.

## 9. Intended End-to-End Flow

```text
1. User submits a request in the frontend.
2. Frontend sends the request to FastAPI.
3. Backend validates and processes the request.
4. Backend invokes the AI inference boundary when required.
5. AI layer selects the configured model.
6. The model generates a response.
7. AI layer returns the structured response.
8. Backend returns the application response.
9. Frontend renders the result.
```

The end-to-end flow should only be marked fully verified after the final API and frontend smoke test passes on merged `main`.

## 10. Evaluation Flow

```text
Model
  |
  +----> AI unit/integration tests
  |
  +----> Model evaluation
  |
  +----> Member 4 QA suite
  |
  +----> Human semantic review
```

Current AI test result:

```text
43 passed
3 skipped
0 failed
```

Current Member 4 QA result:

```text
28 executed
27 automated PASS
1 automated FAIL
0 runtime errors
```

## 11. MLOps Layer

MLOps/experiment tracking covers:

- experiment identity
- model identity
- dataset identity
- parameters
- metrics
- artifacts
- evaluation results
- reproducibility information
- Git source reference

Any reconstruction of a historical run must be explicitly labelled as retrospective tracking.

## 12. Documentation Layer

Documentation is maintained across:

```text
README.md
docs/api/
docs/architecture/
docs/data-engineering/
docs/frontend/
docs/requirements/
```

The documentation should allow a reviewer to trace:

```text
Dataset
  -> Validation
  -> Dataset Release
  -> Model Training
  -> LoRA Adapter
  -> Model Registry
  -> Inference Service
  -> Backend API
  -> Frontend
  -> Evaluation / QA
  -> MLOps
```

## 13. Ownership Boundaries

| Layer | Primary Owner |
|---|---|
| AI / ML | Member 1 |
| Data Engineering | Member 2 |
| Backend + Frontend + Deployment | Member 3 |
| AI Evaluation / QA | Member 4 |
| MLOps / MLflow | Member 5 |
| Documentation | Member 6 |

## 14. Security and Configuration

Secrets and environment-specific configuration remain outside version control.

Examples:

```text
backend/.env
database passwords
API keys
private credentials
```

Never commit credentials or other secrets.

## 15. Current Integration Status

Independently verified:

- AI test suite
- dataset engineering release
- model registry
- AI inference implementation
- local PostgreSQL connectivity

Final system-level validation remains dependent on:

- database migrations
- FastAPI startup
- API inference test
- frontend -> backend -> AI end-to-end smoke test

These should only be marked verified after they pass on the final merged `main` branch.

## 16. Architecture Summary

```text
                        USER
                          |
                          v
                     FRONTEND
                          |
                          v
                     FASTAPI
                    /                          /                           v           v
              DATABASE      AI LAYER
             PostgreSQL        |
                               v
                         MODEL REGISTRY
                      /         |                              /          |                              v           v           v
                 Qwen3       Qwen2.5     SmolLM2
                   |
                   v
               HDFC LoRA
```
