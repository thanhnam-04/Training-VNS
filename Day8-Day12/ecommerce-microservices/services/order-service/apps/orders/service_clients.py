import json
from typing import Any

import requests
from django.conf import settings


class ServiceClientError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _auth_headers(request) -> dict[str, str]:
    # Forward bearer token to downstream services to keep auth context.
    authorization = request.headers.get("Authorization", "")
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    return headers


def fetch_cart_snapshot(request) -> dict[str, Any]:
    # Read cart snapshot before checkout so order data is frozen at checkout time.
    try:
        response = requests.get(
            f"{settings.CART_SERVICE_URL}/api/cart/",
            headers=_auth_headers(request),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise ServiceClientError(f"Cart service unavailable: {exc}") from exc

    if response.status_code != 200:
        raise ServiceClientError("Cannot fetch cart data.", status_code=502)

    return response.json()


def clear_cart(request) -> None:
    # Clear cart only after order and order items are created successfully.
    try:
        response = requests.delete(
            f"{settings.CART_SERVICE_URL}/api/cart/clear/",
            headers=_auth_headers(request),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise ServiceClientError(f"Cart service unavailable: {exc}") from exc

    if response.status_code not in (200, 204):
        raise ServiceClientError("Cannot clear cart.", status_code=502)


def reserve_stock(request, items: list[dict[str, int]]) -> list[dict[str, Any]]:
    # Reserve stock in inventory service to prevent overselling race conditions.
    payload = {"items": items}
    try:
        response = requests.post(
            f"{settings.INVENTORY_SERVICE_URL}/api/inventory/internal/reserve-stock/",
            headers=_auth_headers(request),
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise ServiceClientError(f"Inventory service unavailable: {exc}") from exc

    if response.status_code == 400:
        data = response.json()
        raise ServiceClientError(data.get("error", "Stock validation failed."), status_code=400)

    if response.status_code != 200:
        raise ServiceClientError("Cannot reserve stock.", status_code=502)

    data = response.json()
    return data.get("reserved", [])


def release_stock(request, items: list[dict[str, int]]) -> None:
    # Compensating action used when checkout fails after stock reservation.
    payload = {"items": items}
    try:
        requests.post(
            f"{settings.INVENTORY_SERVICE_URL}/api/inventory/internal/release-stock/",
            headers=_auth_headers(request),
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException:
        # Best effort compensation.
        return
