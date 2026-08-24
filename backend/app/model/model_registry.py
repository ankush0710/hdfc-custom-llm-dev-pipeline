from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Model_Registry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(100), nullable=False)
    base_model = Column(String(100), nullable=False)
    artifact_path = Column(Text, nullable=True)
    adapter_path = Column(Text, nullable=True)
    training_job_id = Column(Integer, ForeignKey("training_job.id"), nullable=True)
    evaluation_id = Column(Integer, ForeignKey("evaluation.evaluation_id"), nullable=True)
    status = Column(String(50), nullable=False, default="CREATED", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

