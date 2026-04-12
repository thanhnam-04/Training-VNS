from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "product_sku", "unit_price", "quantity", "subtotal_display"]

    def subtotal_display(self, obj):
        if not obj.pk or obj.unit_price is None:
            return "—"
        return f"{obj.subtotal:,.0f} ₫"
    subtotal_display.short_description = "Thành tiền"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "user", "status", "status_badge", "payment_method",
                    "total_display", "is_paid", "created_at"]
    list_filter = ["status", "payment_method", "is_paid", "created_at"]
    search_fields = ["order_number", "user__email", "shipping_name", "shipping_phone"]
    readonly_fields = ["order_number", "subtotal", "total_amount", "created_at", "updated_at"]
    list_editable = ["status", "is_paid"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 25
    actions = ["mark_as_confirmed", "mark_as_delivered"]

    def save_model(self, request, obj, form, change):
        """Trigger email khi Admin đổi trạng thái thủ công (qua form hoặc list_editable)"""
        # Lưu thay đổi trước
        super().save_model(request, obj, form, change)
        
        # Nếu đang chỉnh sửa và trường trạng thái có đổi
        if change and "status" in form.changed_data:
            try:
                from apps.notifications.tasks import send_order_status_email
                send_order_status_email.delay(obj.id)
            except Exception:
                pass

    @admin.action(description="📦 Xác nhận các đơn hàng đã chọn")
    def mark_as_confirmed(self, request, queryset):
        orders_to_update = list(queryset.exclude(status="confirmed"))
        updated = queryset.update(status="confirmed")
        try:
            from apps.notifications.tasks import send_order_status_email
            for order in orders_to_update:
                send_order_status_email.delay(order.id)
        except Exception:
            pass
        self.message_user(request, f"✅ Đã xác nhận {updated} đơn hàng thành công.")

    @admin.action(description="🚚 Đánh dấu đã giao cho các đơn hàng")
    def mark_as_delivered(self, request, queryset):
        orders_to_update = list(queryset.exclude(status="delivered"))
        updated = queryset.update(status="delivered")
        try:
            from apps.notifications.tasks import send_order_status_email
            for order in orders_to_update:
                send_order_status_email.delay(order.id)
        except Exception:
            pass
        self.message_user(request, f"✅ Đã đánh dấu giao thành công {updated} đơn hàng.")

    fieldsets = (
        ("Thông tin đơn hàng", {"fields": ("order_number", "user", "status", "is_paid", "payment_method")}),
        ("Giao hàng", {"fields": ("shipping_name", "shipping_phone", "shipping_address", "note")}),
        ("Tài chính", {"fields": ("subtotal", "shipping_fee", "total_amount")}),
        ("Thời gian", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b", "confirmed": "#3b82f6", "processing": "#8b5cf6",
            "shipped": "#06b6d4", "delivered": "#10b981", "cancelled": "#ef4444"
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Trạng thái"

    def total_display(self, obj):
        amount = f"{obj.total_amount:,.0f}" if obj.total_amount else "0"
        return format_html('<strong>{} ₫</strong>', amount)
    total_display.short_description = "Tổng tiền"
    total_display.admin_order_field = "total_amount"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
