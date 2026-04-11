"""
Cart Models — Day 10: One-to-Many, Many-to-Many, Quan hệ phức tạp
Demo: select_related, prefetch_related tối ưu query
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.inventory.models import Product

User = get_user_model()


class Cart(models.Model):
    """Mỗi user có 1 giỏ hàng active — One-to-One với User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                 related_name="cart", verbose_name="Người dùng")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Giỏ hàng"

    def __str__(self):
        return f"Giỏ của {self.user.email}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    """Chi tiết sản phẩm trong giỏ — One-to-Many: Cart → CartItem"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                              related_name="items", verbose_name="Giỏ hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                 related_name="cart_items", verbose_name="Sản phẩm")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sản phẩm trong giỏ"
        verbose_name_plural = "Sản phẩm trong giỏ"
        unique_together = ["cart", "product"]  # Mỗi sản phẩm chỉ xuất hiện 1 lần

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        # Validate số lượng không vượt tồn kho
        if self.quantity > self.product.stock:
            self.quantity = self.product.stock
        super().save(*args, **kwargs)
