import auth
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
app.include_router(auth.router)
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running successfully!"}

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


