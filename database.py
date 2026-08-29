import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# To reload .env file
load_dotenv()

# To read .env from DATABASE_URL 
DATABASE_URL = os.getenv("DATABASE_URL", "......")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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
