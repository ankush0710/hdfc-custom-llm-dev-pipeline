# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Deployment(Base):
    __tablename__ = "deployment"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    model_id = Column(
        Integer,
        ForeignKey(
            "model_registry.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    version = Column(
        String(100),
        nullable=False
    )

    environment = Column(
        String(50),
        nullable=False,
        default="development"
    )

    status = Column(
        String(50),
        nullable=False,
        default="STOPPED"
    )

    endpoint = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
