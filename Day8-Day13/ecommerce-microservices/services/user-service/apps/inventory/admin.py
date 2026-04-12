"""
Inventory Admin — Day 8: Django Admin cực kỳ đầy đủ
Demo: list_display, list_filter, search_fields, inline, actions, readonly_fields
"""
import csv
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, F, DecimalField, ExpressionWrapper
from django.utils.html import format_html
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

# Giảm rủi ro thao tác nhầm trên danh sách.
admin.site.disable_action("delete_selected")
admin.site.site_header = "VNS E-commerce Admin"
admin.site.site_title = "VNS Admin"
admin.site.index_title = "Bảng điều khiển quản trị"


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
    extra = 0
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
                    "stock", "min_stock", "stock_display", "status", "status_badge", "is_featured", "updated_at"]
    list_filter = ["status", "category", "is_featured", LowStockFilter, "created_at"]
    search_fields = ["name", "sku", "description"]
    list_editable = ["stock", "min_stock", "status", "is_featured"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["tags"]
    readonly_fields = ["profit_margin", "created_at", "updated_at", "thumbnail"]
    actions = [export_as_csv]
    inlines = [StockMovementInline]
    list_per_page = 25
    change_list_template = "admin/inventory/product/change_list.html"

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

    def get_queryset(self, request):
        # ORM nâng cao: select_related tránh N+1
        return super().get_queryset(request).select_related("category", "supplier")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        stats = self.get_queryset(request).aggregate(
            total_products=Count("id"),
            active_products=Count("id", filter=Q(status=Product.Status.ACTIVE)),
            low_stock_products=Count("id", filter=Q(stock__gt=0, stock__lte=F("min_stock"))),
            out_of_stock_products=Count("id", filter=Q(stock=0)),
            total_units=Sum("stock"),
            total_inventory_value=Sum(
                ExpressionWrapper(
                    F("stock") * F("price"),
                    output_field=DecimalField(max_digits=18, decimal_places=0),
                )
            ),
        )
        extra_context["product_stats"] = {
            "total_products": stats["total_products"] or 0,
            "active_products": stats["active_products"] or 0,
            "low_stock_products": stats["low_stock_products"] or 0,
            "out_of_stock_products": stats["out_of_stock_products"] or 0,
            "total_units": stats["total_units"] or 0,
            "total_inventory_value": f"{int(stats['total_inventory_value'] or 0):,}",
        }
        return super().changelist_view(request, extra_context=extra_context)


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

    def has_delete_permission(self, request, obj=None):
        return False
