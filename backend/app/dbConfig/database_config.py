import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# import the database url from config
from app.core.config import DATABASE_URL

_debug_echo = os.getenv("DEBUG", "false").lower() == "true"

# creating engine for database
# pool_pre_ping: drop stale Neon connections on checkout
# pool_recycle: recycle connections every 5 minutes (Neon idles out after ~5m)
# pool_size/max_overflow: conservative limits for serverless Neon connection quota
engine = create_engine(
    DATABASE_URL,
    echo=_debug_echo,
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


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

