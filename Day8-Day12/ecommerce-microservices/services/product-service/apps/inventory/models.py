"""
Inventory Models — Day 8: Django Admin + ORM Nâng Cao
Demo: Category, Product, Supplier, StockMovement
ORM: annotate, aggregate, Q, F expressions
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.db.models import F

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Mô tả")
    icon = models.CharField(max_length=50, default="📦", verbose_name="Icon")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icon} {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tag")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên nhà cung cấp")
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Người liên hệ")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="SĐT")
    address = models.TextField(blank=True, verbose_name="Địa chỉ")
    is_active = models.BooleanField(default=True, verbose_name="Hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Đang bán"
        INACTIVE = "inactive", "Ngừng bán"
        OUT_OF_STOCK = "out_of_stock", "Hết hàng"

    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Mô tả")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    price = models.DecimalField(max_digits=12, decimal_places=0,
                                validators=[MinValueValidator(0)], verbose_name="Giá bán (VNĐ)")
    cost_price = models.DecimalField(max_digits=12, decimal_places=0,
                                     validators=[MinValueValidator(0)], verbose_name="Giá vốn")
    stock = models.PositiveIntegerField(default=0, verbose_name="Tồn kho")
    min_stock = models.PositiveIntegerField(default=5, verbose_name="Tồn kho tối thiểu")
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="Ảnh")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                  related_name="products", verbose_name="Danh mục")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="products", verbose_name="Nhà cung cấp")
    tags = models.ManyToManyField(Tag, blank=True, related_name="products", verbose_name="Tags")
    status = models.CharField(max_length=20, choices=Status.choices,
                               default=Status.ACTIVE, verbose_name="Trạng thái")
    is_featured = models.BooleanField(default=False, verbose_name="Nổi bật")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Auto cập nhật status theo stock
        if self.stock == 0:
            self.status = self.Status.OUT_OF_STOCK
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock and self.stock > 0

    @property
    def profit_margin(self):
        if self.price and self.cost_price and self.price > 0:
            return round(((self.price - self.cost_price) / self.price) * 100, 1)
        return 0

    def __str__(self):
        return f"[{self.sku}] {self.name}"


class StockMovement(models.Model):
    """Lịch sử nhập/xuất kho — demo ORM aggregate"""
    class MovementType(models.TextChoices):
        IN = "in", "Nhập kho"
        OUT = "out", "Xuất kho"
        ADJUSTMENT = "adjustment", "Điều chỉnh"
        RETURN = "return", "Trả hàng"

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                 related_name="movements", verbose_name="Sản phẩm")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices,
                                      verbose_name="Loại")
    quantity = models.IntegerField(verbose_name="Số lượng")  # âm = xuất
    note = models.CharField(max_length=300, blank=True, verbose_name="Ghi chú")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    verbose_name="Người thực hiện")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Biến động kho"
        verbose_name_plural = "Biến động kho"
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.product.name} | {sign}{self.quantity} | {self.get_movement_type_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # F() expression: atomic update tồn kho
        Product.objects.filter(pk=self.product_id).update(
            stock=F("stock") + self.quantity
        )
