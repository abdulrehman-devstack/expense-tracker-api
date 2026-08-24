from database import Base  # database.py se main base class mangwayi
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
)  # MySQL ki datatypes import kiye


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