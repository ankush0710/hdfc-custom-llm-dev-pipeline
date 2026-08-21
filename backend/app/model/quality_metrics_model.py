from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Quality_Model(Base):
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, ForeignKey("processing_job.id", ondelete="CASCADE"), nullable=False)

    total_rows = Column(Integer, default=0)

    total_columns = Column(Integer, default=0)
    
    duplicate_rows = Column(Integer, default=0)

    missing_values = Column(Integer, default=0)

    empty_rows = Column(Integer, default=0)

    quality_check = Column(Integer, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
