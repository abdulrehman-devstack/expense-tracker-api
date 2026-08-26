from datetime import datetime,date
from typing import Optional
from pydantic import BaseModel, EmailStr ,Field

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
    
class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    category: str
    date: date
    note: Optional[str] = None


# Create Schema (User jab naya expense submit karega)
class ExpenseCreate(ExpenseBase):
    pass


# Response Schema (API jab response mein expense wapas bhejegi)
class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True