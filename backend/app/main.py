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
from app.routes.pipeline_routes.pipeline_routes import router as pipeline_router


from app.routes.auth_routes.auth_routes import router as auth_router


Base.metadata.create_all(bind=engine)

def _seed_initial_admin():
    """Seed initial default ADMIN user securely and idempotently."""
    import os
    from app.dbConfig.database_config import SessionLocal
    from app.model.user_model import User_Model
    from app.core.auth_dependency import hash_password, verify_password

    admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "ankushkurvey053@gmail.com").lower().strip()
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "ankush@1234")
    admin_name = os.getenv("INITIAL_ADMIN_NAME", "Ankush Kurvey (System Admin)")

    db = SessionLocal()
    try:
        # 1. Clean up legacy seed account if present
        legacy_admin = db.query(User_Model).filter(User_Model.email == "ankushkurvey@053").first()
        if legacy_admin and legacy_admin.email != admin_email:
            db.delete(legacy_admin)
            db.commit()

        # 2. Seed or update required initial ADMIN account
        admin_user = db.query(User_Model).filter(User_Model.email == admin_email).first()
        if not admin_user:
            admin_user = User_Model(
                full_name=admin_name,
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="ADMIN",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
        else:
            # Ensure proper role, active status and valid password hash
            updated = False
            if admin_user.role != "ADMIN":
                admin_user.role = "ADMIN"
                updated = True
            if not admin_user.is_active:
                admin_user.is_active = True
                updated = True
            if not verify_password(admin_password, admin_user.password_hash):
                admin_user.password_hash = hash_password(admin_password)
                updated = True
            if updated:
                db.commit()
    except Exception as exc:
        db.rollback()
    finally:
        db.close()

_seed_initial_admin()

app = FastAPI(
    title = "HDFC Custom llm Development Pipeline API",
    version = "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
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

@app.get("/")
def root():
    return {
        "message": "HDFC Custom LLM Pipeline API is running"
    }
