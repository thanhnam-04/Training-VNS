"""
Inventory Admin — Day 8: Django Admin cực kỳ đầy đủ
Demo: list_display, list_filter, search_fields, inline, actions, readonly_fields
"""
import csv
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Tag, Supplier, Product, StockMovement


def export_as_csv(modeladmin, request, queryset):
    """Custom Admin Action: Xuất CSV"""
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={meta}.csv"
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response

export_as_csv.short_description = "📥 Xuất CSV"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["icon", "name", "slug", "product_count", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]
    readonly_fields = ["created_at"]

    def product_count(self, obj):
        count = obj.products.filter(status="active").count()
        color = "green" if count > 0 else "gray"
        return format_html('<span style="color:{}">{} sản phẩm</span>', color, count)
    product_count.short_description = "Sản phẩm"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "product_count"]
    search_fields = ["name"]

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "# Sản phẩm"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_name", "email", "phone", "product_count", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "contact_name", "email", "phone"]
    list_editable = ["is_active"]
    readonly_fields = ["created_at"]
    actions = [export_as_csv]

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "# Sản phẩm"


class StockMovementInline(admin.TabularInline):
    """Inline biến động kho trong trang Product"""
    model = StockMovement
    extra = 1
    fields = ["movement_type", "quantity", "note", "created_by", "created_at"]
    readonly_fields = ["created_at"]
    classes = ["collapse"]


class LowStockFilter(admin.SimpleListFilter):
    """Custom filter: lọc sản phẩm tồn kho thấp"""
    title = "Tồn kho thấp"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return [("yes", "⚠️ Sắp hết hàng")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            from django.db.models import F
            return queryset.filter(stock__lte=F("min_stock"), stock__gt=0)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "name", "sku", "category", "price_display",
                    "stock_display", "status_badge", "is_featured", "updated_at"]
    list_filter = ["status", "category", "is_featured", LowStockFilter, "created_at"]
    search_fields = ["name", "sku", "description"]
    list_editable = ["is_featured"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["tags"]
    readonly_fields = ["profit_margin", "created_at", "updated_at", "thumbnail"]
    actions = [export_as_csv, "mark_featured", "mark_inactive"]
    inlines = [StockMovementInline]
    list_per_page = 25

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("name", "slug", "sku", "description", "image", "thumbnail")
        }),
        ("Giá & Tồn kho", {
            "fields": ("price", "cost_price", "profit_margin", "stock", "min_stock")
        }),
        ("Phân loại", {
            "fields": ("category", "supplier", "tags", "status", "is_featured")
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:4px"/>', obj.image.url)
        return "—"
    thumbnail.short_description = "Ảnh"

    def price_display(self, obj):
        amount = f"{obj.price:,.0f}"
        return format_html('<strong>{} ₫</strong>', amount)
    price_display.short_description = "Giá bán"
    price_display.admin_order_field = "price"

    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:red;font-weight:bold">Hết hàng</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color:orange">⚠️ {}</span>', obj.stock)
        return format_html('<span style="color:green">{}</span>', obj.stock)
    stock_display.short_description = "Tồn kho"
    stock_display.admin_order_field = "stock"

    def status_badge(self, obj):
        colors = {"active": "green", "inactive": "gray", "out_of_stock": "red"}
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Trạng thái"

    @admin.action(description="⭐ Đánh dấu nổi bật")
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"✅ Đã đánh dấu {updated} sản phẩm nổi bật.")

    @admin.action(description="🚫 Ngừng bán")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=Product.Status.INACTIVE)
        self.message_user(request, f"⛔ Đã ngừng bán {updated} sản phẩm.")

    def get_queryset(self, request):
        # ORM nâng cao: select_related tránh N+1
        return super().get_queryset(request).select_related("category", "supplier")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["product", "movement_type", "quantity_display", "note", "created_by", "created_at"]
    list_filter = ["movement_type", "created_at"]
    search_fields = ["product__name", "product__sku", "note"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["product"]   # Requires search_fields on ProductAdmin ✓
    date_hierarchy = "created_at"
    list_per_page = 30

    def quantity_display(self, obj):
        color = "green" if obj.quantity > 0 else "red"
        sign = "+" if obj.quantity > 0 else ""
        return format_html('<span style="color:{};font-weight:bold">{}{}</span>', color, sign, obj.quantity)
    quantity_display.short_description = "Số lượng"
