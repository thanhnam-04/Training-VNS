from typing import Iterable

from fastapi import Depends, HTTPException

from app.core.dependencies import get_current_user
from app.core.roles import UserRole
from app.models.user import User


class RoleChecker:
    def __init__(self, allowed_roles: Iterable[UserRole | str]):
        self.allowed_roles = {
            role.value if isinstance(role, UserRole) else str(role)
            for role in allowed_roles
        }

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            allowed = ", ".join(sorted(self.allowed_roles))
            raise HTTPException(status_code=403, detail=f"Required role(s): {allowed}")
        return current_user
