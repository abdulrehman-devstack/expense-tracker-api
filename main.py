from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from database import get_db
from models import Expense, Income, Budget ,User
from email_utils import send_budget_alert
from sqlalchemy import func

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExpenseSchema(BaseModel):
    title: str
    amount: float
    category: str
    date: date
    note: Optional[str] = None

class IncomeSchema(BaseModel):
    source: str
    amount: float
    date: date
    note: Optional[str] = None

class BudgetSchema(BaseModel):
    category: str
    monthly_limit: float


@app.get("/expenses/")
def get_expenses(user_id: int, db: Session = Depends(get_db)):
    return db.query(Expense).filter(Expense.user_id == user_id).all()

@app.post("/expenses/")
def create_expense(user_id: int, expense: ExpenseSchema, db: Session = Depends(get_db)):
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date,
        note=expense.note,
        user_id=user_id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    budget = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == expense.category
    ).first()

    if budget:
        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.category == expense.category
        ).scalar() or 0.0

        if total_spent > float(budget.monthly_limit):
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.email:
                send_budget_alert(
                    to_email=user.email,
                    category=expense.category,
                    limit=float(budget.monthly_limit),
                    total_spent=float(total_spent)
                )

    return new_expense

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, user_id: int, expense: ExpenseSchema, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db_expense.title = expense.title
    db_expense.amount = expense.amount
    db_expense.category = expense.category
    db_expense.date = expense.date
    db_expense.note = expense.note
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return {"message": "Deleted successfully"}


@app.get("/incomes/")
def get_incomes(user_id: int, db: Session = Depends(get_db)):
    return db.query(Income).filter(Income.user_id == user_id).all()

@app.post("/incomes/")
def create_income(user_id: int, income: IncomeSchema, db: Session = Depends(get_db)):
    new_income = Income(
        source=income.source,
        amount=income.amount,
        date=income.date,
        note=income.note,
        user_id=user_id
    )
    db.add(new_income)
    db.commit()
    db.refresh(new_income)
    return new_income

@app.put("/incomes/{income_id}")
def update_income(income_id: int, user_id: int, income: IncomeSchema, db: Session = Depends(get_db)):
    db_income = db.query(Income).filter(Income.id == income_id, Income.user_id == user_id).first()
    if not db_income:
        raise HTTPException(status_code=404, detail="Income not found")
    
    db_income.source = income.source
    db_income.amount = income.amount
    db_income.date = income.date
    db_income.note = income.note
    db.commit()
    db.refresh(db_income)
    return db_income

@app.delete("/incomes/{income_id}")
def delete_income(income_id: int, db: Session = Depends(get_db)):
    db_income = db.query(Income).filter(Income.id == income_id).first()
    if not db_income:
        raise HTTPException(status_code=404, detail="Income not found")
    db.delete(db_income)
    db.commit()
    return {"message": "Deleted successfully"}


@app.get("/budgets/")
def get_budgets(user_id: int, db: Session = Depends(get_db)):
    return db.query(Budget).filter(Budget.user_id == user_id).all()

@app.post("/budgets/")
def create_or_update_budget(user_id: int, budget: BudgetSchema, db: Session = Depends(get_db)):
    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category == budget.category
    ).first()

    if existing:
        existing.monthly_limit = budget.monthly_limit
        db.commit()
        db.refresh(existing)
        return existing

    new_budget = Budget(
        user_id=user_id,
        category=budget.category,
        monthly_limit=budget.monthly_limit
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget

@app.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    db_budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(db_budget)
    db.commit()
    return {"message": "Deleted successfully"}