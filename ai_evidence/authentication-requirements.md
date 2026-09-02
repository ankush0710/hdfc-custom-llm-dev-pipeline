# Authentication & Authorization Requirements

## Ownership

The ML module does not currently implement user authentication.

FastAPI/backend owns:
- authentication
- authorization
- token validation
- role checking
- endpoint protection

## Logical application roles

| Role | Dataset | Training | Evaluation | Model/Deployment |
|---|---|---|---|---|
| Admin | Full | Full | Full | Full |
| Data Scientist | Read/Write | Run | Run/View | View |
| Reviewer | Read | No | View/Approve | Approve/View |
| Developer | Read | Limited/No | View | View |

The backend may map these roles to its chosen identity provider.

## Model artifacts

Model binaries and adapter files must never be returned directly to the browser. FastAPI should expose metadata/internal references instead.
