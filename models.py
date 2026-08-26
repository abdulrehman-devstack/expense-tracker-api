from database import Base  # database.py se main base class mangwayi
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
     Column, Date, ForeignKey, Integer, Numeric, String, Text
)  # MySQL ki datatypes import kiye
from sqlalchemy.orm import relationship



class User(Base):  # Python ko bataya ke hum 'User' naam ka table bana rahe hain
    __tablename__ = "users"  # MySQL database mein table ka naam "users" hoga

    id = Column(
        Integer, primary_key=True, index=True
    )  # Har user ki unique Number ID (1, 2, 3...)
    email = Column(
        String(255), unique=True, index=True, nullable=False
    )  # Email address (Do users ka same email nahi ho sakta)
    hashed_password = Column(
        String(255), nullable=False
    )  # Encrypted password yahan save hoga
    is_active = Column(
        Boolean, default=True
    )  # Status ke user account active hai ya blocked (True/False)
    
    class Expense(Base):
        __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship: Har expense kisi na kisi user se linked hoga
    owner = relationship("User", back_populates="expenses")


# User model mein bhi yeh relationship line add kar do:
# User.expenses = relationship("Expense", back_populates="owner")