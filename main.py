import auth
from auth import get_current_user
from database import Base, engine ,get_db
import models
import schemas
from sqlalchemy.orm import Session
from fastapi import FastAPI , APIRouter, Depends, HTTPException, status

# MySQL mein tables generate karne ke liye
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/expenses", tags=["Expenses"])

app = FastAPI(title="Expense Tracker API")

# Authentication Endpoints Include Kar Rahe Hain


@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running successfully!"}

# @app.get("/expenses/", response_model=list[schemas.ExpenseResponse])
# def get_expenses(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#     return db.query(models.Expense).filter(models.Expense.owner_id == current_user.id).all()

# PUT: Update an existing expense

# 1. GET /expenses/ - Logged-in user ke tamam expenses fetch karne ke liye
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

@router.post(
    "/",
    response_model=schemas.ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(get_current_user) # Pass logged-in user id
    user_id: int = 1,  # Temporary testing user_id until auth middleware is passed
):
    new_expense = models.Expense(**expense.model_dump(), user_id=user_id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


# 3. PUT /expenses/{expense_id} - Expense Update Karne Ke Liye
@router.put("/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    updated_expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user_id: int = 1,
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

    expense_query.update(
        dict(updated_expense), synchronize_session=False
    )  # Direct dict() wrapper
    db.commit()
    return expense_query.first()

# 4. DELETE /expenses/{expense_id} - Expense Delete Karne Ke Liye
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
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

# 5. GET /expenses/analytics - Expenses Summary & Totals
@router.get("/analytics", response_model=schemas.AnalyticsResponse)
def get_expense_analytics(
    db: Session = Depends(get_db),
    user_id: int = 1,
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

app.include_router(auth.router)
app.include_router(router)