from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.core.rbac import RoleChecker
from app.core.roles import UserRole
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas import Token, TokenValidationResponse, UserCreate, UserResponse, UserRoleUpdate

router = APIRouter(prefix="/api/auth", tags=["Auth"])

require_admin = RoleChecker([UserRole.ADMIN])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    username_exists = await db.execute(select(User).where(User.username == user.username))
    if username_exists.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    email_exists = await db.execute(select(User).where(User.email == user.email))
    if email_exists.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_count = await db.execute(select(User))
    # Bootstrap policy: first account becomes admin, others default to user.
    role = UserRole.ADMIN.value if not user_count.scalars().first() else UserRole.USER.value

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
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/internal/validate-token", response_model=TokenValidationResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}


@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(User).order_by(User.id.asc()))
    return result.scalars().all()


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    next_role = payload.role.value
    if target_user.id == current_admin.id and next_role != UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail="Cannot remove admin role from yourself")

    if target_user.role == UserRole.ADMIN.value and next_role != UserRole.ADMIN.value:
        admin_count_result = await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN.value))
        admin_count = admin_count_result.scalar_one()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="At least one admin account is required")

    target_user.role = next_role
    await db.commit()
    await db.refresh(target_user)
    return target_user
