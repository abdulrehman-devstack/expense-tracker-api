from datetime import datetime,date
from typing import Optional
from pydantic import BaseModel, EmailStr ,Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    # is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    category: str
    date: date
    note: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
        
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