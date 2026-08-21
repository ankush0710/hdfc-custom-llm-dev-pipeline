# ====================================================================================
# Model for dataset processing after upload to validate the dataset model
# ====================================================================================

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Processing_Model(Base):
    __tablename__ = "processing_job"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer, 
        ForeignKey("dataset.id", ondelete="CASCADE"),
        nullable=False
    )

    status = Column(String(50), nullable=False, default="PENDING")

    input_file = Column(String, nullable=True)

    output_file = Column(String, nullable=True)

    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
