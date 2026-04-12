import os
import time

import requests

BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_EMAIL = os.environ.get("SMOKE_ADMIN_EMAIL", "admin@shopvns.com")
ADMIN_PASSWORD = os.environ.get("SMOKE_ADMIN_PASSWORD", "Admin@123")
REQUEST_TIMEOUT = 10
STARTUP_TIMEOUT = 90


def _url(path: str) -> str:
    return f"{BASE_URL}{path}"


def _wait_for_endpoint(path: str) -> None:
    deadline = time.time() + STARTUP_TIMEOUT
    last_error = ""

    while time.time() < deadline:
        try:
            response = requests.get(_url(path), timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code}, body={response.text[:200]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(2)

    raise AssertionError(
        f"Service endpoint {path} is not ready after {STARTUP_TIMEOUT}s: {last_error}"
    )


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_health_endpoints_all_services() -> None:
    health_paths = [
        "/health/user",
        "/health/product",
        "/health/cart",
        "/health/order",
        "/health/notification",
    ]

    for health_path in health_paths:
        _wait_for_endpoint(health_path)
        response = requests.get(_url(health_path), timeout=REQUEST_TIMEOUT)

        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") == "ok"


def test_auth_login_returns_access_and_refresh_tokens() -> None:
    response = requests.post(
        _url("/api/auth/login/"),
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=REQUEST_TIMEOUT,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("access")
    assert payload.get("refresh")


def test_core_endpoints_reachable_with_auth() -> None:
    login_response = requests.post(
        _url("/api/auth/login/"),
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=REQUEST_TIMEOUT,
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access"]
    headers = _auth_headers(access_token)

    inventory_response = requests.get(
        _url("/api/inventory/products/"),
        timeout=REQUEST_TIMEOUT,
    )
    assert inventory_response.status_code == 200

    cart_response = requests.get(
        _url("/api/cart/"),
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    assert cart_response.status_code == 200

    orders_response = requests.get(
        _url("/api/orders/"),
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    assert orders_response.status_code == 200
