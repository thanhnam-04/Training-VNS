"""
Orders Models — Day 10 & 12: Many-to-Many qua OrderItem (Through Model)
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.inventory.models import Product

User = get_user_model()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ xác nhận"
        CONFIRMED = "confirmed", "Đã xác nhận"
        PROCESSING = "processing", "Đang xử lý"
        SHIPPED = "shipped", "Đang giao"
        DELIVERED = "delivered", "Đã giao"
        CANCELLED = "cancelled", "Đã hủy"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Thanh toán khi nhận hàng"
        BANK = "bank", "Chuyển khoản ngân hàng"
        MOMO = "momo", "Ví MoMo"

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name="orders", verbose_name="Khách hàng")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Mã đơn")
    status = models.CharField(max_length=20, choices=Status.choices,
                               default=Status.PENDING, verbose_name="Trạng thái")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices,
                                       default=PaymentMethod.COD, verbose_name="Thanh toán")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")

    # Địa chỉ giao hàng (snapshot tại thời điểm đặt)
    shipping_name = models.CharField(max_length=100, verbose_name="Tên người nhận")
    shipping_phone = models.CharField(max_length=20, verbose_name="SĐT giao hàng")
    shipping_address = models.TextField(verbose_name="Địa chỉ giao hàng")

    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=30000)
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    note = models.TextField(blank=True, verbose_name="Ghi chú")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.order_number} — {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"VNS{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Day 10: Many-to-Many thông qua Through Model
    Product ↔ Order qua OrderItem (với extra fields: price, quantity)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                               related_name="items", verbose_name="Đơn hàng")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True,
                                 related_name="order_items", verbose_name="Sản phẩm")
    product_name = models.CharField(max_length=200)   # Snapshot tên sản phẩm
    product_sku = models.CharField(max_length=50)      # Snapshot SKU
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)  # Snapshot giá
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết đơn hàng"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def subtotal(self):
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity
