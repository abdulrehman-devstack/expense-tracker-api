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
    # is_active: bool

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
        
# Analytics / Summary Response Schema
class AnalyticsResponse(BaseModel):
    total_spent: float
    total_count: int
    category_breakdown: dict[str, float]
    
    
class IncomeBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    source: str
    date: date
    note: Optional[str] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeResponse(IncomeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
        
class BudgetBase(BaseModel):
    category: str
    monthly_limit: float = Field(..., gt=0, description="Budget limit must be greater than zero")


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True