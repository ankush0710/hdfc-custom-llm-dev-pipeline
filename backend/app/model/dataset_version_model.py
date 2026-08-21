# ====================================================================================
# Model for dataset version
# ====================================================================================

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.dbConfig.database_config import Base


class Dataset_Version_Model(Base):
    __tablename__ = "dataset_version"

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "version",
            name="uq_dataset_version"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dataset_id = Column(
        Integer,
        ForeignKey(
            "dataset.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    version = Column(
        String(50),
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    file_size = Column(
        Float,
        nullable=False
    )

    file_type = Column(
        String(50),
        nullable=False
    )

    file_hash = Column(
        String(128),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="Uploaded"
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

    dataset = relationship(
        "Dataset_Model",
        back_populates="versions"
    )

    processing_jobs = relationship(
        "Processing_Model",
        back_populates="dataset_version",
        cascade="all, delete-orphan"
    )