import auth
from auth import get_current_user
from database import Base, engine, get_db
import models
import schemas
from sqlalchemy.orm import Session
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from email_utils import send_budget_alert

# MySQL mein tables generate karne ke liye
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

# Routers Define
router = APIRouter(prefix="/expenses", tags=["Expenses"])
income_router = APIRouter(prefix="/incomes", tags=["Incomes"])
budget_router = APIRouter(prefix="/budgets", tags=["Budgets"])

@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running successfully!"}

# 1. EXPENSE ENDPOINTS

@router.get("/", response_model=list[schemas.ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Expense)
        .filter(models.Expense.user_id == current_user.id)
        .all()
    )


@router.post("/", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: schemas.ExpenseCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    new_expense = models.Expense(**expense.model_dump(), user_id=user_id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.category == expense.category
    ).all()
    
    total_spent = 0.0
    for exp in expenses:
        total_spent += float(getattr(exp, "amount", 0))

    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.category == expense.category
    ).first()

    if budget is not None and total_spent > float(getattr(budget, "limit", 0)):
        send_budget_alert(
            to_email="abdulrehman.devstack@gmail.com",
            category=str(expense.category),
            limit=float(getattr(budget, "limit", 0)),
            total_spent=total_spent
        )

    return new_expense


@router.put("/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    updated_expense: schemas.ExpenseCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    expense_query = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.user_id == user_id
    )
    db_expense = expense_query.first()

    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense nahi mila",
        )

    expense_query.update(dict(updated_expense), synchronize_session=False)
    db.commit()
    return expense_query.first()


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    expense_query = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.user_id == user_id
    )
    db_expense = expense_query.first()

    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense nahi mila",
        )

    expense_query.delete(synchronize_session=False)
    db.commit()
    return None


@router.get("/analytics", response_model=schemas.AnalyticsResponse)
def get_expense_analytics(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    expenses = db.query(models.Expense).filter(models.Expense.user_id == user_id).all()

    if not expenses:
        return {
            "total_spent": 0.0,
            "total_count": 0,
            "category_breakdown": {}
        }

    total_spent = sum(float(getattr(e, "amount", 0)) for e in expenses)
    total_count = len(expenses)

    category_breakdown: dict[str, float] = {}
    for e in expenses:
        cat = str(getattr(e, "category", "Other"))
        amt = float(getattr(e, "amount", 0))
        category_breakdown[cat] = category_breakdown.get(cat, 0.0) + amt

    return {
        "total_spent": total_spent,
        "total_count": total_count,
        "category_breakdown": category_breakdown
    }


# 2. INCOME ENDPOINTS

@income_router.get("/", response_model=list[schemas.IncomeResponse])
def get_incomes(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    return db.query(models.Income).filter(models.Income.user_id == user_id).all()


@income_router.post("/", response_model=schemas.IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    income: schemas.IncomeCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    new_income = models.Income(**income.model_dump(), user_id=user_id)
    db.add(new_income)
    db.commit()
    db.refresh(new_income)
    return new_income


# 3. BUDGET ENDPOINTS

@budget_router.post("/", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
def set_budget(
    budget: schemas.BudgetCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    existing_budget: models.Budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.category == budget.category
    ).first()

    if existing_budget:
        existing_budget.limit = budget.monthly_limit
        db.commit()
        db.refresh(existing_budget)
        return existing_budget

    new_budget = models.Budget(**budget.model_dump(), user_id=user_id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


@budget_router.get("/", response_model=list[schemas.BudgetResponse])
def get_budgets(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    return db.query(models.Budget).filter(models.Budget.user_id == user_id).all()


# INCLUDE ROUTERS IN APP (END OF FILE)

app.include_router(auth.router)
app.include_router(router)
app.include_router(income_router)
app.include_router(budget_router)