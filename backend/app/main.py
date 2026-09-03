# pyrefly: ignore [missing-import]
import logging
import os
import sys
from pathlib import Path

# Ensure repo root and backend directory are in sys.path
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
_backend_root = str(Path(__file__).resolve().parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
import app.model  # noqa: F401 — registers all ORM models with Base

from app.routes.dataset_routes.dataset_routes import router as dataset_router
from app.routes.processing_routes.processing_routes import router as processing_router
from app.routes.training_routes.training_routes import router as training_router
from app.routes.training_job_routes.training_job_routes import router as training_job_router
from app.routes.evaluation_routes.evaluation_routes import router as evaluation_router
from app.routes.model_registry_routes.model_registry_routes import router as model_registry_router
from app.routes.deployment_routes.deployment_routes import router as deployment_router
from app.routes.inference_routes.inference_routes import router as inference_router
from app.routes.ai_routes.ai_routes import router as ai_router
from app.routes.pipeline_routes.pipeline_routes import router as pipeline_router
from app.routes.auth_routes.auth_routes import router as auth_router

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_env = os.getenv("ENVIRONMENT", "development").lower()
_is_production = _env == "production"

# ---------------------------------------------------------------------------
# Admin seed — credentials from environment only
# ---------------------------------------------------------------------------
def _seed_initial_admin():

    from app.dbConfig.database_config import SessionLocal
    from app.model.user_model import User_Model
    from app.core.auth_dependency import hash_password, verify_password

    admin_email = (os.getenv("INITIAL_ADMIN_EMAIL") or "").lower().strip()
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD") or ""
    admin_name = os.getenv("INITIAL_ADMIN_NAME", "System Admin")

    if not admin_email or not admin_password:
        _logger.warning(
            "INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD not set — skipping admin seed."
        )
        return

    db = SessionLocal()
    try:
        user = db.query(User_Model).filter(User_Model.email == admin_email).first()
        if not user:
            user = User_Model(
                full_name=admin_name,
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="ADMIN",
                is_active=True,
            )
            db.add(user)
            db.commit()
            _logger.info("Admin user seeded: %s", admin_email)
        else:
            updated = False
            if user.role != "ADMIN":
                user.role = "ADMIN"
                updated = True
            if not user.is_active:
                user.is_active = True
                updated = True
            if not verify_password(admin_password, user.password_hash):
                user.password_hash = hash_password(admin_password)
                updated = True
            if updated:
                db.commit()
                
    except Exception as exc:
        _logger.error("Admin seed failed: %s", exc)
        db.rollback()
    finally:
        db.close()


_seed_initial_admin()

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOW_ORIGINS") or os.getenv("ALLOW_ORIGIN") or ""
_allowed_origins = [
    origin.strip().rstrip("/")
    for origin in _raw_origins.split(",")
    if origin.strip()
]

_raw_origin_regex = (os.getenv("ALLOW_ORIGIN_REGEX") or "").strip()
_origin_regex = _raw_origin_regex if _raw_origin_regex else None

if not _allowed_origins and not _origin_regex:
    _logger.warning(
        "Neither ALLOW_ORIGINS nor ALLOW_ORIGIN_REGEX is configured. "
        "Browser requests from external frontend origins will be blocked by CORS."
    )

app = FastAPI(
    title="HDFC Custom LLM Development Pipeline API",
    version="1.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    max_age=600,
)

app.include_router(auth_router)
app.include_router(dataset_router)
app.include_router(processing_router)
app.include_router(training_router)
app.include_router(training_job_router)
app.include_router(evaluation_router)
app.include_router(model_registry_router)
app.include_router(deployment_router)
app.include_router(inference_router)
app.include_router(ai_router)
app.include_router(pipeline_router)


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(OperationalError)
async def db_operational_error_handler(request: Request, exc: OperationalError):
    _logger.error(f"Database operational error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Database connection is temporarily unreachable. Please retry shortly."},
    )


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "HDFC Custom LLM Pipeline API is running", "environment": _env}


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe for load balancers and container orchestration."""
    from app.dbConfig.database_config import SessionLocal
    from sqlalchemy import text
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "unreachable",
        },
    )
