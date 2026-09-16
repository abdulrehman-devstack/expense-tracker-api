import io
from datetime import date, datetime
from typing import List

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from database import Base, engine, get_db
from models import Budget, Expense, Income, User
from email_utils import send_budget_alert
import auth
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/", include_in_schema=False)
def serve_login():
    return FileResponse("index.html")


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    return FileResponse("dashboard.html")


@app.get("/style.css", include_in_schema=False)
def serve_css():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    return FileResponse("app.js", media_type="application/javascript")

@app.get("/expenses/", response_model=List[schemas.ExpenseResponse])
def get_expenses(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Expense).filter(Expense.user_id == current_user.id).all()


@app.post("/expenses/", response_model=schemas.ExpenseResponse)
def create_expense(
    expense: schemas.ExpenseCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date,
        note=expense.note,
        user_id=current_user.id,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    budget = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category == expense.category,
    ).first()

    if budget:
        today = date.today()
        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.category == expense.category,
            extract("month", Expense.date) == today.month,
            extract("year", Expense.date) == today.year,
        ).scalar() or 0.0

        if float(total_spent) > float(budget.monthly_limit):
            if current_user.email:
                send_budget_alert(
                    to_email=current_user.email,
                    category=expense.category,
                    limit=float(budget.monthly_limit),
                    total_spent=float(total_spent),
                )

    return new_expense


@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    expense: schemas.ExpenseCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
    ).first()
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
def delete_expense(
    expense_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
    ).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return {"message": "Deleted successfully"}

@app.get("/expenses/report/excel")
def export_expenses_excel(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.date.desc()).all()

    if not expenses:
        raise HTTPException(status_code=404, detail="No expense records found to export")

    data = [{
        "ID": e.id,
        "Title": e.title,
        "Amount": float(e.amount),
        "Category": e.category,
        "Date": str(e.date),
        "Note": e.note or "",
    } for e in expenses]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Expenses")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Expense_Report.xlsx"'},
    )

@app.get("/expenses/report/pdf")
def export_expenses_pdf(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.date.desc()).all()

    if not expenses:
        raise HTTPException(status_code=404, detail="No expense records found to export")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30,
    )
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        f"<b>Expense Report</b><br/>User: {current_user.email}<br/>"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Title"],
    )
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    table_data = [["ID", "Title", "Category", "Amount ($)", "Date", "Note"]]
    total = 0.0
    for e in expenses:
        table_data.append([
            str(e.id),
            e.title[:20],
            e.category[:15],
            f"{float(e.amount):.2f}",
            str(e.date),
            (e.note or "")[:20],
        ])
        total += float(e.amount)

    table_data.append(["", "", "", f"TOTAL: {total:.2f}", "", ""])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F2F2")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D5F5E3")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Expense_Report.pdf"'},
    )

@app.get("/incomes/", response_model=List[schemas.IncomeResponse])
def get_incomes(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Income).filter(Income.user_id == current_user.id).all()


@app.post("/incomes/", response_model=schemas.IncomeResponse)
def create_income(
    income: schemas.IncomeCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    new_income = Income(
        source=income.source,
        amount=income.amount,
        date=income.date,
        note=income.note,
        user_id=current_user.id,
    )
    db.add(new_income)
    db.commit()
    db.refresh(new_income)
    return new_income


@app.put("/incomes/{income_id}", response_model=schemas.IncomeResponse)
def update_income(
    income_id: int,
    income: schemas.IncomeCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id,
    ).first()
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
def delete_income(
    income_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id,
    ).first()
    if not db_income:
        raise HTTPException(status_code=404, detail="Income not found")
    db.delete(db_income)
    db.commit()
    return {"message": "Deleted successfully"}

@app.get("/budgets/", response_model=List[schemas.BudgetResponse])
def get_budgets(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Budget).filter(Budget.user_id == current_user.id).all()


@app.post("/budgets/", response_model=schemas.BudgetResponse)
def create_or_update_budget(
    budget: schemas.BudgetCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category == budget.category,
    ).first()

    if existing:
        existing.monthly_limit = budget.monthly_limit
        db.commit()
        db.refresh(existing)
        return existing

    new_budget = Budget(
        user_id=current_user.id,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


@app.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
    ).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(db_budget)
    db.commit()
    return {"message": "Deleted successfully"}

@app.get("/analytics/summary", response_model=schemas.AnalyticsResponse)
def get_summary(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    incomes = db.query(Income).filter(Income.user_id == current_user.id).all()

    total_spent = sum(float(e.amount) for e in expenses)
    total_income = sum(float(i.amount) for i in incomes)
    total_count = len(expenses)
    avg_expense = (total_spent / total_count) if total_count else 0.0

    category_breakdown: dict = {}
    for e in expenses:
        category_breakdown[e.category] = (
            category_breakdown.get(e.category, 0.0) + float(e.amount)
        )

    return {
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "balance": round(total_income - total_spent, 2),
        "total_count": total_count,
        "average_expense": round(avg_expense, 2),
        "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
    }