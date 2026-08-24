import bcrypt
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
import models
import schemas
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Helper Functions: Direct bcrypt use kar rahe hain
def hash_password(password: str) -> str:
    # Password ko bytes mein convert karke hash karte hain
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


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
    # Check karo agar email pehle se exist karti hai
    db_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    if db_user:
        raise HTTPException(
            status_code=400, detail="Email already registered!"
        )

    # Password Hash karo aur Naya User Database mein Save karo
    hashed_pwd = hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user