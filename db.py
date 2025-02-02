from sqlalchemy import (
    create_engine,
    Column,
    String,
    Boolean,
    Integer,
    TIMESTAMP,
    JSON,
    ForeignKey,
)
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


# Define Odds table
class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(100), unique=True, nullable=False)
    sport_key = Column(String(100), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    commence_time = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP)


# Define Bookmakers table
class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id = Column(Integer, primary_key=True, index=True)
    odds_id = Column(Integer, ForeignKey("odds.id"), nullable=False)
    bookmaker_key = Column(String(100), nullable=False)
    bookmaker_title = Column(String(255), nullable=False)
    last_update = Column(TIMESTAMP, nullable=False)
    market_type = Column(String(50), nullable=False)
    market_outcome_name = Column(String(100), nullable=False)
    market_outcome_price = Column(String(50), nullable=True)
    market_point = Column(String(50), nullable=True)


# Initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)
