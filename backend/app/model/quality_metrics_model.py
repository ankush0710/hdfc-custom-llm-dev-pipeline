from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.dbConfig.database_config import Base

class Quality_Metrics(Base):
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer)



