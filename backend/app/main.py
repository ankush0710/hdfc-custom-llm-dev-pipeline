from fastapi import FastAPI

from app.db.database import Base, engine
from app.db import model


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "HDFC Custom llm Development Pipeline API",
    version = "1.0.0"
)

@app.get("/")
def root():
    return{
        "message": "HDFC Bank Custom LL Pipeline API is running...."
    }

@app.get("/health")
def get_health():
    return {
        "status":"health ok"
    }