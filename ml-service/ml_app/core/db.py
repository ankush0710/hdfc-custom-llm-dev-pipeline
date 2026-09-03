"""
ml-service/app/core/db.py

Database session manager for the ML Service to persist real-time training and evaluation telemetry
directly into Neon PostgreSQL.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
else:
    engine = None
    SessionLocal = None
    logger.warning("DATABASE_URL is not configured; ML worker will run without direct database persistence.")


def get_ml_db():
    """Dependency for obtaining a database session in ML service routes if needed."""
    if not SessionLocal:
        raise RuntimeError("Database connection not configured in ML Service.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
