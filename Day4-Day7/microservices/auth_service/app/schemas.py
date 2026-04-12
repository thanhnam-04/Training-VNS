from typing import Optional
from pydantic import BaseModel, EmailStr

from app.core.roles import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenValidationResponse(BaseModel):
    id: int
    username: str
    role: str


class UserRoleUpdate(BaseModel):
    role: UserRole
