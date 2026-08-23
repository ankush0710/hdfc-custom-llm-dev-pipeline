from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.constants.training_status import training_status


from app.dbConfig.database_config import Base

class Training_Model(Base):
    __tablename__ = "training_run"

    id = Column(Integer, primary_key=True, index=True, nullable=False)

    dataset_version_id = Column(Integer, ForeignKey("dataset_version.id"), nullable=False)

    base_model = Column(String, nullable=False)

    training_method = Column(String, nullable=False)

    epochs = Column(Integer, nullable=False)

    learning_rate = Column(Float, nullable=False)

    batch_size = Column(Integer, nullable=False)

    status = Column(String, nullable=False, default=training_status.CREATED)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    started_at = Column(DateTime(timezone=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    #relationships
    evaluations = relationship(
        "Evaluation_Model",
        back_populates="training_run"
    )
