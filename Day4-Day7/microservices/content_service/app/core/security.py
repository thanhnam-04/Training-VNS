from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.clients.auth_client import validate_token_with_auth_service
from app.schemas import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    return await validate_token_with_auth_service(token)
