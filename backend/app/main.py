from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.dbConfig.database_config import Base, engine
from app.routes.dataset_routes.dataset_routes import router as dataset_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "HDFC Custom llm Development Pipeline API",
    version = "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = "http://localhost:3000",
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True
)

app.include_router(dataset_router)

@app.get("/")
def root():
    return {
        "message": "HDFC Custom LLM Pipeline API is running"
    }
