from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, ForeignKey)
from sqlalchemy.orm import relationship
from app.dbConfig.databse_config import Base

class Model_Model(Base):
    __tablename__ = "model"

    model_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_family = Column(String(100), nullable=False)
    base_model = Column(String(100), nullable=False)
    fine_tuned = Column(Boolean, nullable=False, default=False)
    status = Column(String(30), nullable=False, default="CREATED")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)