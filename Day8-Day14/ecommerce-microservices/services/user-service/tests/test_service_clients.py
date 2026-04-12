from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from apps.orders import service_clients as clients


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def _request_with_auth(token: str | None = "Bearer test-token") -> SimpleNamespace:
    headers = {}
    if token is not None:
        headers["Authorization"] = token
    return SimpleNamespace(headers=headers)


def test_auth_headers_include_authorization() -> None:
    request = _request_with_auth("Bearer abc")

    headers = clients._auth_headers(request)

    assert headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer abc",
    }


def test_auth_headers_without_authorization() -> None:
    request = _request_with_auth(None)

    headers = clients._auth_headers(request)

    assert headers == {"Content-Type": "application/json"}


def test_fetch_cart_snapshot_success(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.settings, "CART_SERVICE_URL", "http://cart-service")
    get_mock = mocker.patch.object(
        clients.requests,
        "get",
        return_value=FakeResponse(200, {"items": [{"product_id": 1}]}),
    )

    result = clients.fetch_cart_snapshot(request)

    assert result == {"items": [{"product_id": 1}]}
    get_mock.assert_called_once_with(
        "http://cart-service/api/cart/",
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-token"},
        timeout=10,
    )


def test_fetch_cart_snapshot_unavailable_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(
        clients.requests,
        "get",
        side_effect=requests.RequestException("connection failed"),
    )

    with pytest.raises(clients.ServiceClientError, match="Cart service unavailable") as exc:
        clients.fetch_cart_snapshot(request)

    assert exc.value.status_code == 502


def test_fetch_cart_snapshot_non_200_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.requests, "get", return_value=FakeResponse(500, {}))

    with pytest.raises(clients.ServiceClientError, match="Cannot fetch cart data") as exc:
        clients.fetch_cart_snapshot(request)

    assert exc.value.status_code == 502


@pytest.mark.parametrize("status_code", [200, 204])
def test_clear_cart_success(mocker, status_code: int) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.settings, "CART_SERVICE_URL", "http://cart-service")
    delete_mock = mocker.patch.object(
        clients.requests,
        "delete",
        return_value=FakeResponse(status_code, {}),
    )

    clients.clear_cart(request)

    delete_mock.assert_called_once_with(
        "http://cart-service/api/cart/clear/",
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-token"},
        timeout=10,
    )


def test_clear_cart_unavailable_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(
        clients.requests,
        "delete",
        side_effect=requests.RequestException("timeout"),
    )

    with pytest.raises(clients.ServiceClientError, match="Cart service unavailable") as exc:
        clients.clear_cart(request)

    assert exc.value.status_code == 502


def test_clear_cart_non_200_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.requests, "delete", return_value=FakeResponse(500, {}))

    with pytest.raises(clients.ServiceClientError, match="Cannot clear cart") as exc:
        clients.clear_cart(request)

    assert exc.value.status_code == 502


def test_reserve_stock_success(mocker) -> None:
    request = _request_with_auth()
    items = [{"product_id": 1, "quantity": 2}]
    mocker.patch.object(clients.settings, "INVENTORY_SERVICE_URL", "http://inventory-service")
    post_mock = mocker.patch.object(
        clients.requests,
        "post",
        return_value=FakeResponse(200, {"reserved": [{"product_id": 1, "quantity": 2}]}),
    )

    result = clients.reserve_stock(request, items)

    assert result == [{"product_id": 1, "quantity": 2}]
    post_mock.assert_called_once_with(
        "http://inventory-service/api/inventory/internal/reserve-stock/",
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-token"},
        data='{"items": [{"product_id": 1, "quantity": 2}]}',
        timeout=15,
    )


def test_reserve_stock_returns_default_empty_list(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.requests, "post", return_value=FakeResponse(200, {}))

    result = clients.reserve_stock(request, [{"product_id": 1, "quantity": 1}])

    assert result == []


def test_reserve_stock_400_raises_with_detail(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(
        clients.requests,
        "post",
        return_value=FakeResponse(400, {"error": "Not enough stock"}),
    )

    with pytest.raises(clients.ServiceClientError, match="Not enough stock") as exc:
        clients.reserve_stock(request, [{"product_id": 1, "quantity": 99}])

    assert exc.value.status_code == 400


def test_reserve_stock_400_raises_default_message(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.requests, "post", return_value=FakeResponse(400, {}))

    with pytest.raises(clients.ServiceClientError, match="Stock validation failed") as exc:
        clients.reserve_stock(request, [{"product_id": 1, "quantity": 99}])

    assert exc.value.status_code == 400


def test_reserve_stock_non_200_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.requests, "post", return_value=FakeResponse(503, {}))

    with pytest.raises(clients.ServiceClientError, match="Cannot reserve stock") as exc:
        clients.reserve_stock(request, [{"product_id": 1, "quantity": 1}])

    assert exc.value.status_code == 502


def test_reserve_stock_unavailable_raises(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(
        clients.requests,
        "post",
        side_effect=requests.RequestException("inventory timeout"),
    )

    with pytest.raises(clients.ServiceClientError, match="Inventory service unavailable") as exc:
        clients.reserve_stock(request, [{"product_id": 1, "quantity": 1}])

    assert exc.value.status_code == 502


def test_release_stock_success(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(clients.settings, "INVENTORY_SERVICE_URL", "http://inventory-service")
    post_mock = mocker.patch.object(clients.requests, "post", return_value=FakeResponse(200, {}))

    clients.release_stock(request, [{"product_id": 1, "quantity": 2}])

    post_mock.assert_called_once_with(
        "http://inventory-service/api/inventory/internal/release-stock/",
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-token"},
        data='{"items": [{"product_id": 1, "quantity": 2}]}',
        timeout=15,
    )


def test_release_stock_best_effort_on_exception(mocker) -> None:
    request = _request_with_auth()
    mocker.patch.object(
        clients.requests,
        "post",
        side_effect=requests.RequestException("release error"),
    )

    # Should not raise because release is best-effort compensation.
    clients.release_stock(request, [{"product_id": 1, "quantity": 2}])
