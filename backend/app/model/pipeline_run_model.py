from sqlalchemy import (Column, Integer, String, DateTime, Float, ForeignKey)
from sqlalchemy.orm import relationship
from app.dbConfig.database_config import Base


class Pipeline_Run_Model(Base):
    __tablename__ = "pipeline_run"

    run_id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset.id"), nullable=False, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_version.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("model.model_id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="QUEUED")
    progress = Column(Float, nullable=True, default=0)
    current_step = Column(String(50), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimate_completion = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(255), nullable=True)


    