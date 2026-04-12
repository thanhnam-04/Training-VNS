from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from apps.notifications import tasks


@dataclass
class FakeOrderItem:
    product_name: str
    quantity: int
    subtotal: int


@dataclass
class FakeUser:
    email: str
    full_name: str = "Test User"


class FakeItemCollection:
    def __init__(self, items: list[FakeOrderItem]) -> None:
        self._items = items

    def all(self) -> list[FakeOrderItem]:
        return self._items


class FakeOrder:
    def __init__(self) -> None:
        self.order_number = "ODR-1001"
        self.user = FakeUser(email="buyer@example.com")
        self.items = FakeItemCollection(
            [
                FakeOrderItem(product_name="Keyboard", quantity=1, subtotal=500000),
                FakeOrderItem(product_name="Mouse", quantity=2, subtotal=300000),
            ]
        )
        self.subtotal = 800000
        self.shipping_fee = 30000
        self.total_amount = 830000
        self.shipping_address = "123 Test Street"
        self.shipping_name = "Nguyen Van A"
        self.shipping_phone = "0900000000"
        self.created_at = datetime(2026, 1, 1, 8, 0, 0)

    def get_payment_method_display(self) -> str:
        return "COD"

    def get_status_display(self) -> str:
        return "Dang giao"


class FakeOrderQuery:
    def __init__(self, order: FakeOrder | None = None, error: Exception | None = None) -> None:
        self._order = order
        self._error = error

    def select_related(self, *_args: object, **_kwargs: object) -> "FakeOrderQuery":
        return self

    def prefetch_related(self, *_args: object, **_kwargs: object) -> "FakeOrderQuery":
        return self

    def get(self, **_kwargs: object) -> FakeOrder:
        if self._error is not None:
            raise self._error
        if self._order is None:
            raise RuntimeError("No fake order configured")
        return self._order


def _inject_fake_order_model(fake_order_model: type) -> None:
    fake_module = types.ModuleType("apps.orders.models")
    fake_module.Order = fake_order_model
    sys.modules["apps.orders.models"] = fake_module


def _inject_fake_inventory_product_model(fake_product_model: type) -> None:
    fake_module = types.ModuleType("apps.inventory.models")
    fake_module.Product = fake_product_model
    sys.modules["apps.inventory.models"] = fake_module


def test_send_order_confirmation_email_sends_to_customer() -> None:
    class FakeOrderModel:
        DoesNotExist = type("DoesNotExist", (Exception,), {})
        objects = FakeOrderQuery(order=FakeOrder())

    _inject_fake_order_model(FakeOrderModel)

    with patch.object(tasks, "send_mail") as send_mail_mock:
        result = tasks.send_order_confirmation_email.run(order_id=20)

    assert result == {
        "status": "sent",
        "order_number": "ODR-1001",
        "email": "buyer@example.com",
    }
    send_mail_mock.assert_called_once()


def test_send_order_confirmation_email_handles_order_not_found() -> None:
    does_not_exist = type("DoesNotExist", (Exception,), {})

    class FakeOrderModel:
        DoesNotExist = does_not_exist
        objects = FakeOrderQuery(error=does_not_exist("missing"))

    _inject_fake_order_model(FakeOrderModel)

    result = tasks.send_order_confirmation_email.run(order_id=21)

    assert result == {"status": "order_not_found", "order_id": 21}


def test_send_order_confirmation_email_retries_on_unexpected_error() -> None:
    class FakeOrderModel:
        DoesNotExist = type("DoesNotExist", (Exception,), {})
        objects = FakeOrderQuery(error=ValueError("smtp down"))

    _inject_fake_order_model(FakeOrderModel)

    retry_error = RuntimeError("retry called")
    retry_mock = Mock(side_effect=retry_error)

    with patch.object(tasks.send_order_confirmation_email, "retry", retry_mock):
        with pytest.raises(RuntimeError, match="retry called"):
            tasks.send_order_confirmation_email.run(order_id=22)

    retry_mock.assert_called_once()


def test_send_order_status_email_sends_update_to_customer() -> None:
    class FakeOrderModel:
        DoesNotExist = type("DoesNotExist", (Exception,), {})
        objects = FakeOrderQuery(order=FakeOrder())

    _inject_fake_order_model(FakeOrderModel)

    with patch.object(tasks, "send_mail") as send_mail_mock:
        result = tasks.send_order_status_email.run(order_id=30)

    assert result == {"status": "sent", "order_number": "ODR-1001"}
    send_mail_mock.assert_called_once()


def test_send_order_status_email_handles_order_not_found() -> None:
    does_not_exist = type("DoesNotExist", (Exception,), {})

    class FakeOrderModel:
        DoesNotExist = does_not_exist
        objects = FakeOrderQuery(error=does_not_exist("missing"))

    _inject_fake_order_model(FakeOrderModel)

    result = tasks.send_order_status_email.run(order_id=31)

    assert result == {"status": "order_not_found"}


def test_send_order_status_email_retries_on_unexpected_error() -> None:
    class FakeOrderModel:
        DoesNotExist = type("DoesNotExist", (Exception,), {})
        objects = FakeOrderQuery(error=ValueError("db error"))

    _inject_fake_order_model(FakeOrderModel)

    retry_error = RuntimeError("retry called")
    retry_mock = Mock(side_effect=retry_error)

    with patch.object(tasks.send_order_status_email, "retry", retry_mock):
        with pytest.raises(RuntimeError, match="retry called"):
            tasks.send_order_status_email.run(order_id=32)

    retry_mock.assert_called_once()


def test_send_low_stock_alert_returns_no_admins() -> None:
    class FakeProduct:
        name = "Laptop"
        sku = "LP-01"
        stock = 2
        min_stock = 5

    class FakeProductManager:
        def get(self, **_kwargs: object) -> FakeProduct:
            return FakeProduct()

    class FakeProductModel:
        objects = FakeProductManager()

    class FakeUserQuerySet:
        def values_list(self, *_args: object, **_kwargs: object) -> list[str]:
            return []

    class FakeUserManager:
        def filter(self, **_kwargs: object) -> FakeUserQuerySet:
            return FakeUserQuerySet()

    fake_user_model = SimpleNamespace(objects=FakeUserManager())

    _inject_fake_inventory_product_model(FakeProductModel)

    with patch("django.contrib.auth.get_user_model", return_value=fake_user_model):
        with patch.object(tasks, "send_mail") as send_mail_mock:
            result = tasks.send_low_stock_alert.run(product_id=40)

    assert result == {"status": "no_admins"}
    send_mail_mock.assert_not_called()


def test_send_low_stock_alert_sends_email_to_admins() -> None:
    class FakeProduct:
        name = "Laptop"
        sku = "LP-01"
        stock = 2
        min_stock = 5

    class FakeProductManager:
        def get(self, **_kwargs: object) -> FakeProduct:
            return FakeProduct()

    class FakeProductModel:
        objects = FakeProductManager()

    class FakeUserQuerySet:
        def values_list(self, *_args: object, **_kwargs: object) -> list[str]:
            return ["admin@example.com"]

    class FakeUserManager:
        def filter(self, **_kwargs: object) -> FakeUserQuerySet:
            return FakeUserQuerySet()

    fake_user_model = SimpleNamespace(objects=FakeUserManager())

    _inject_fake_inventory_product_model(FakeProductModel)

    with patch("django.contrib.auth.get_user_model", return_value=fake_user_model):
        with patch.object(tasks, "send_mail") as send_mail_mock:
            result = tasks.send_low_stock_alert.run(product_id=41)

    assert result == {"status": "sent", "product": "Laptop"}
    send_mail_mock.assert_called_once()


def test_send_low_stock_alert_retries_on_unexpected_error() -> None:
    class FakeProductManager:
        def get(self, **_kwargs: object) -> object:
            raise ValueError("product query error")

    class FakeProductModel:
        objects = FakeProductManager()

    _inject_fake_inventory_product_model(FakeProductModel)

    retry_error = RuntimeError("retry called")
    retry_mock = Mock(side_effect=retry_error)

    with patch.object(tasks.send_low_stock_alert, "retry", retry_mock):
        with pytest.raises(RuntimeError, match="retry called"):
            tasks.send_low_stock_alert.run(product_id=42)

    retry_mock.assert_called_once()


def test_generate_inventory_report_returns_aggregated_stats() -> None:
    expected = {"total_products": 10, "out_of_stock": 1, "low_stock": 2}

    class FakeProductManager:
        def aggregate(self, **_kwargs: object) -> dict[str, int]:
            return expected

    class FakeProductModel:
        objects = FakeProductManager()

    _inject_fake_inventory_product_model(FakeProductModel)

    result = tasks.generate_inventory_report.run()

    assert result == expected


def test_resize_product_image_returns_no_image() -> None:
    class FakeProduct:
        name = "No Image Product"
        image = None

    class FakeProductManager:
        def get(self, **_kwargs: object) -> FakeProduct:
            return FakeProduct()

    class FakeProductModel:
        objects = FakeProductManager()

    _inject_fake_inventory_product_model(FakeProductModel)

    result = tasks.resize_product_image.run(product_id=50)

    assert result == {"status": "no_image"}


def test_resize_product_image_success() -> None:
    class FakeImageField:
        path = "/tmp/product.jpg"

    class FakeProduct:
        name = "Image Product"
        image = FakeImageField()

    class FakeProductManager:
        def get(self, **_kwargs: object) -> FakeProduct:
            return FakeProduct()

    class FakeProductModel:
        objects = FakeProductManager()

    class FakeImageContext:
        def __enter__(self) -> "FakeImageContext":
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

        def thumbnail(self, *_args: object, **_kwargs: object) -> None:
            return None

        def save(self, *_args: object, **_kwargs: object) -> None:
            return None

    class FakeImageModule:
        LANCZOS = "lanczos"

        @staticmethod
        def open(_path: str) -> FakeImageContext:
            return FakeImageContext()

    _inject_fake_inventory_product_model(FakeProductModel)

    fake_pil_module = types.ModuleType("PIL")
    fake_pil_module.Image = FakeImageModule

    with patch.dict(sys.modules, {"PIL": fake_pil_module}):
        result = tasks.resize_product_image.run(product_id=51)

    assert result == {"status": "resized", "product": "Image Product"}


def test_resize_product_image_retries_on_unexpected_error() -> None:
    class FakeProductManager:
        def get(self, **_kwargs: object) -> object:
            raise ValueError("image processing failed")

    class FakeProductModel:
        objects = FakeProductManager()

    _inject_fake_inventory_product_model(FakeProductModel)

    retry_error = RuntimeError("retry called")
    retry_mock = Mock(side_effect=retry_error)

    with patch.object(tasks.resize_product_image, "retry", retry_mock):
        with pytest.raises(RuntimeError, match="retry called"):
            tasks.resize_product_image.run(product_id=52)

    retry_mock.assert_called_once()
