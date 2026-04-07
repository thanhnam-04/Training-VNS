from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User
from app.schemas import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token


async def register_user(db: AsyncSession, user: UserCreate) -> User:
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    result_email = await db.execute(select(User).where(User.email == user.email))
    if result_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = get_password_hash(user.password)
    user_count = await db.execute(select(User))
    role = "admin" if not user_count.scalars().first() else "user"

    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_pass,
        role=role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def login_user(db: AsyncSession, username: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
