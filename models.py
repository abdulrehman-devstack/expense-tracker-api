from database import Base
from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    expenses = relationship("Expense", back_populates="owner")
    incomes = relationship("Income", back_populates="owner")
    budgets = relationship("Budget", back_populates="owner")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Linking with User model
    owner = relationship("User", back_populates="expenses")
    
class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    source = Column(String(100), nullable=False) 
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="incomes")
    
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Numeric(10, 2), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="budgets")