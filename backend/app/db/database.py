from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# import the database url from config 
from app.core.config import DATABASE_URL

# creating engine for database 
engine = create_engine(
    DATABASE_URL,
    echo= True
)

sessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine,
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

