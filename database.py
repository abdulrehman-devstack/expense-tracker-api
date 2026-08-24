import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# .env file load karna
load_dotenv()

# .env se DATABASE_URL read karna
DATABASE_URL = os.getenv("mysql+pymysql://root:ar4729189@localhost/expense_tracker")

# MySQL Connection Engine
engine = create_engine("mysql+pymysql://root:ar4729189@localhost/expense_tracker", pool_pre_ping=True)

# Database Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for Models
Base = declarative_base()


# Database Dependency for FastAPI Endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()