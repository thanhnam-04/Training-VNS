from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import create_access_token, decode_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas import Token, TokenValidationResponse, UserCreate, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    username_exists = await db.execute(select(User).where(User.username == user.username))
    if username_exists.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    email_exists = await db.execute(select(User).where(User.email == user.email))
    if email_exists.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_count = await db.execute(select(User))
    role = "admin" if not user_count.scalars().first() else "user"

    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=get_password_hash(user.password),
        role=role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def me(authorization: str = Header(default=""), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/internal/validate-token", response_model=TokenValidationResponse)
async def validate_token(authorization: str = Header(default=""), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": user.id, "username": user.username, "role": user.role}
