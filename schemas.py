from datetime import date
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class ExpenseBase(BaseModel):
    title: str = Field(default="Untitled")
    amount: float = Field(..., gt=0)
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

class IncomeBase(BaseModel):
    amount: float = Field(..., gt=0)
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
    monthly_limit: float = Field(..., gt=0)


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_spent: float
    total_income: float
    balance: float
    total_count: int
    average_expense: float
    category_breakdown: Dict[str, float]