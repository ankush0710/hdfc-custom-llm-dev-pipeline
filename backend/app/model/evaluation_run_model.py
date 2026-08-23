from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.dbConfig.database_config import Base

class Evaluation_Model(Base):
    __tablename__ = "evaluation"

    evaluation_id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_run.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("model.model_id"), nullable=False, index=True)
    test_dataset_id = Column(Integer, ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False, index=True)
    total_examples = Column(Integer, nullable=False, default=0)
    evaluation_status = Column(String(50), nullable=False, default="QUEUED")

    # metrics
    intent_json_validity = Column(Float, nullable=True)
    intent_structured_accuracy = Column(Float, nullable=True)
    answer_accuracy = Column(Float, nullable=True)
    citation_accuracy = Column(Float, nullable=True)
    policy_flag_accuracy = Column(Float, nullable=True)
    escalation_accuracy = Column(Float, nullable=True)
    full_structured_match = Column(Float, nullable=True)
    normalized_exact_match = Column(Float, nullable=True)
    critical_safety_failures = Column(Integer, nullable=True, default=0)
    infrastructure_errors = Column(Integer, nullable=True, default=0)
    average_latency_seconds = Column(Float, nullable=True)

    # status tracking & timestampe
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    pipeline_run = relationship("Pipeline_Run_Model", back_populates="evaluations")
