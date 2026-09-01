from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
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

    # Real-time trainer metrics persisted per step by the progress callback
    train_loss = Column(Float, nullable=True)       # latest training loss from SFTTrainer
    current_lr = Column(Float, nullable=True)       # current learning rate
    current_step = Column(Integer, nullable=True)   # current global_step from trainer state
    max_steps = Column(Integer, nullable=True)      # total steps (state.max_steps) from trainer
    # JSON array of {"step", "pct", "loss", "lr", "ts"} objects for sparkline charts
    log_entries = Column(Text, nullable=True)