# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.dbConfig.database_config import Base, engine
import app.model
from app.routes.dataset_routes.dataset_routes import router as dataset_router
from app.routes.processing_routes.processing_routes import router as processing_router
from app.routes.training_routes.training_routes import router as training_router
from app.routes.training_job_routes.training_job_routes import router as training_job_router
from app.routes.evaluation_routes.evaluation_routes import router as evaluation_router
from app.routes.model_registry_routes.model_registry_routes import router as model_registry_router
from app.routes.deployment_routes.deployment_routes import router as deployment_router
from app.routes.inference_routes.inference_routes import router as inference_router
from app.routes.ai_routes.ai_routes import router as ai_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "HDFC Custom llm Development Pipeline API",
    version = "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True
)

app.include_router(dataset_router)
app.include_router(processing_router)
app.include_router(training_router)
app.include_router(training_job_router)
app.include_router(evaluation_router)
app.include_router(model_registry_router)
app.include_router(deployment_router)
app.include_router(inference_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {
        "message": "HDFC Custom LLM Pipeline API is running"
    }
