# ====================================================================================
# Model for dataset upload model
# ====================================================================================


from datetime import datetime
from sqlalchemy import  Column, DateTime, Float, Integer, String, Text
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

    version = Column(
        String(50),
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

    file_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable = False
    )

    file_size = Column(
        Float,
        nullable=False
    )

    file_type = Column(
        String(50),
        nullable = False
    )

    status = Column(
        String(50),
        nullable = False,
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


