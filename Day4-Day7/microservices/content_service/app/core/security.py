from typing import Sequence

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.clients.auth_client import validate_token_with_auth_service
from app.schemas import CurrentUser
from app.core.roles import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    return await validate_token_with_auth_service(token)


class RoleChecker:
    def __init__(self, allowed_roles: Sequence[str]):
        self.allowed_roles = set(allowed_roles)

    def ensure_allowed(self, current_user: CurrentUser) -> None:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Operation not permitted. Allowed roles: {sorted(self.allowed_roles)}",
            )

    def ensure_owner_or_allowed(self, current_user: CurrentUser, owner_id: int) -> None:
        # Owner can access own resource; privileged role can bypass ownership.
        if current_user.id == owner_id:
            return
        self.ensure_allowed(current_user)

    def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        self.ensure_allowed(current_user)
        return current_user


admin_role_checker = RoleChecker([UserRole.ADMIN.value])
