from sqlalchemy import create_engine, Column, String, Boolean, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Load DB URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize DB connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Sports table
class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    sport_key = Column(String(100), unique=True, nullable=False)
    group_name = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    active = Column(Boolean, default=False, nullable=False)
    has_outrights = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP)

# Initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)
