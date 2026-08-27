import bcrypt
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
import models
import schemas
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Helper Functions: Direct Use bcrypt 
def hash_password(password: str) -> str:
    # To convert password into bytes and write in hash
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

# Temporary Helper for Testing
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found in DB. Please register a user first.")
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# 1. SIGNUP ENDPOINT
@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
   #@ check if Email exist
    db_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    if db_user:
        raise HTTPException(
            status_code=400, detail="Email already registered!"
        )

    # Hash the password nad safe into database
    hashed_pwd = hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user