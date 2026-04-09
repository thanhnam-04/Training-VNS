import os
import httpx
from fastapi import HTTPException

from app.schemas import CurrentUser

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")


async def validate_token_with_auth_service(token: str) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{AUTH_SERVICE_URL}/api/auth/internal/validate-token",
            headers={"Authorization": f"Bearer {token}"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    return CurrentUser(**response.json())
