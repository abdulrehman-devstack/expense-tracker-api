from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

# 1. Signup / User Creation Schema
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# 2. Login Request Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 3. User Response Schema (Password wapas nahi bhejte!)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True

# 4. Token Response Schema
class Token(BaseModel):
    access_token: str
    token_type: str