from sqlalchemy import Column, Integer, String, Flot, DateTime, ForeignKey
from sqlalchemy.sql import func


from app.dbConfig.db_config import Base

class Training_Model(Base):
    __tablename__ = "training_run"

    id = Column(Integer, primary_key=True, index=True, nullable=False)

    dataset_version_id = Column(Integer, ForeignKey("dataset_version.id"), nullable=False)

    base_model = Column(String, nullable=False)

    training_method = Column(String, nullabe=False)

    epochs = Column(Integer, nullable=False)

    learning_rate = Column(Float, nullable=False)

    batch_size = Column(Integer, nullable=False)

    status = Column(String, nullable=False, default="CREATED")

    error_message = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    started_at = Column(DateTime(timezon=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)

