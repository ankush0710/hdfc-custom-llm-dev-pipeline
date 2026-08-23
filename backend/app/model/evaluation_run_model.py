from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, ForeignKey)
from sqlalchemy.orm import relationship
from app.dbConfig.databse_config import Base

class Evaluation_Model(Base):
    __tablename__ = "evaluation"

    evaluation_id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_run.run_id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("model.model_id"), nullable=False, index=True)
    test_dataset_id = Column(Integer, ForeignKey("dataset.dataset_id"), nullable=False, index=True)
    total_examples = Column(Integer, nullable=False, default=0)

    # metrics
    intent_json_validity = Column(Float, nullable=False)
    intent_structured_accuracy = Column(Float, nullable=False)
    answer_accuracy = Column(Float, nullable=False)
    citation_accuracy = Column(Float, nullable=False)
    policy_flag_accuracy = Column(Float, nullable=False)
    escalation_accuracy = Column(Float, nullable=False)
    full_structured_match = Column(Float, nullable=False)
    normalized_exact_match = Column(Float, nullable=False)
    critical_safety_failures = Column(Integer, nullable=False)
    infrastructure_errors = Column(Integer, nullable=False)
    average_latency_seconds = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # relationship
    pipeline_run = relationship("Pipeline_Run_Model", back_populates="evaluation")