from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.dbConfig.database_config import Base

class Quality_Model(Base):
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, ForeignKey("processing_job.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    total_rows = Column(Integer, default=0)

    total_columns = Column(Integer, default=0)
    
    duplicate_rows = Column(Integer, default=0)

    missing_values = Column(Integer, default=0)

    empty_rows = Column(Integer, default=0)

    quality_score = Column(Float, default=0.0)

    pii_instances_detected = Column(Integer, default=0)

    pii_types_detected = Column(String(500), default="NONE")

    records_sanitized = Column(Integer, default=0)

    is_safe_for_training = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    processing_job = relationship("Processing_Model", back_populates="quality_metrics")