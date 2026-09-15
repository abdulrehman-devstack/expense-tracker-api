import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Default: SQLite (local development)
# Railway pe: DATABASE_URL environment variable PostgreSQL dega
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expense_tracker.db")

# SQLite ke liye special setting zaroori hai
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — har request ke liye DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()