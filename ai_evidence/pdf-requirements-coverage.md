# PDF Requirements Coverage

DS-side package now covers:
- workflow and lifecycle
- pipeline inputs/outputs
- dataset schema and validation
- preprocessing
- training configuration
- evaluation schema/methodology/metrics
- model metadata and registry
- artifact information
- inference API contract
- pipeline statuses
- ML error contract
- long-running job guidance
- environment
- sample data/responses
- minimum integration test dataset
- database ML fields
- logging contract
- authentication requirements
- data/model lineage

Backend-owned implementation remains:
- FastAPI endpoints
- Pydantic models
- PostgreSQL migrations/persistence
- authentication implementation
- queue/orchestration
- Swagger/OpenAPI
- production Docker image
- Next.js integration
