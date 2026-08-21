# ====================================================================================
# Model for dataset upload model
# ====================================================================================


from datetime import datetime
from sqlalchemy import  Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Dataset_Model(Base):
    __tablename__ = "dataset"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dataset_name = Column(
        String(255),
        nullable=False
    )

    category = Column(
        String(100),
        nullable = False
    )

    source = Column(
        String(255),
        nullable = False
    )

    description = Column(
        Text,
        nullable = True
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

    versions = relationship(
        "Dataset_Version_Model",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )


