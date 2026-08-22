from sqlalchemy import (Column, String, Integer, DateTime, ForeignKey, Text)
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base
from app.constants.training_status import training_status

class TrainingJobModel(Base):
    __tablename__ = "training_job"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    training_run_id = Column(Integer, ForeignKey("training_run.id"), nullable=False)
    status = Column(String, nullable=False, default=training_status.QUEUED)
    worker_id = Column(String, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    