from sqlalchemy import Column, Integer, String

from app.core.database import Base
from app.core.roles import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    password_hash = Column(String)
    role = Column(String, default=UserRole.USER.value)
