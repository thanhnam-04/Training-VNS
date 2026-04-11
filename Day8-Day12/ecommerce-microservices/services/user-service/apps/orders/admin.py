from django.contrib import admin
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import path, reverse
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
    change_list_template = "admin/orders/order/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "stats/",
                self.admin_site.admin_view(self.stats_view),
                name="orders_order_stats",
            ),
        ]
        return custom_urls + urls

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

    def _quick_links_context(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        changelist_url = reverse("admin:orders_order_changelist")
        return {
            "orders_stats_url": reverse("admin:orders_order_stats"),
            "orders_pending_url": f"{changelist_url}?status__exact={Order.Status.PENDING}",
            "orders_unpaid_url": f"{changelist_url}?is_paid__exact=0",
            "orders_today_url": (
                f"{changelist_url}?created_at__gte={today.isoformat()}&created_at__lt={tomorrow.isoformat()}"
            ),
            "orders_delivered_url": f"{changelist_url}?status__exact={Order.Status.DELIVERED}",
            "orders_all_url": changelist_url,
        }

    def _build_analytics_context(self, queryset):
        today = timezone.localdate()
        week_start = today - timedelta(days=6)
        month_start = today.replace(day=1)

        non_cancelled = queryset.exclude(status=Order.Status.CANCELLED)
        delivered = queryset.filter(status=Order.Status.DELIVERED)
        paid_non_cancelled = queryset.filter(is_paid=True).exclude(status=Order.Status.CANCELLED)

        order_stats = queryset.aggregate(
            total_orders=Count("id"),
            paid_orders=Count("id", filter=Q(is_paid=True)),
            cancelled_orders=Count("id", filter=Q(status=Order.Status.CANCELLED)),
        )
        total_revenue = non_cancelled.aggregate(value=Sum("total_amount"))["value"] or 0
        delivered_revenue = delivered.aggregate(value=Sum("total_amount"))["value"] or 0
        paid_revenue = paid_non_cancelled.aggregate(value=Sum("total_amount"))["value"] or 0
        revenue_today = non_cancelled.filter(created_at__date=today).aggregate(value=Sum("total_amount"))["value"] or 0
        revenue_month = non_cancelled.filter(created_at__date__gte=month_start).aggregate(value=Sum("total_amount"))["value"] or 0

        non_cancelled_count = non_cancelled.count()
        avg_order_value = int(total_revenue / non_cancelled_count) if non_cancelled_count else 0

        total_orders = order_stats["total_orders"] or 0
        cancelled_orders = order_stats["cancelled_orders"] or 0
        cancellation_rate = round((cancelled_orders / total_orders) * 100, 1) if total_orders else 0

        payment_rows_raw = list(
            paid_non_cancelled.values("payment_method")
            .annotate(orders=Count("id"), revenue=Sum("total_amount"))
            .order_by("-revenue")
        )
        payment_label_map = dict(Order.PaymentMethod.choices)
        payment_rows = [
            {
                "label": payment_label_map.get(row["payment_method"], row["payment_method"]),
                "orders": row["orders"],
                "revenue": f"{int(row['revenue'] or 0):,}",
            }
            for row in payment_rows_raw
        ]

        daily_rows_raw = list(
            non_cancelled.filter(created_at__date__gte=week_start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(orders=Count("id"), revenue=Sum("total_amount"))
            .order_by("day")
        )
        daily_map = {row["day"]: row for row in daily_rows_raw}
        daily_rows = []
        for offset in range(0, 7):
            day = week_start + timedelta(days=offset)
            row = daily_map.get(day, {"orders": 0, "revenue": 0})
            daily_rows.append(
                {
                    "day": day.strftime("%d/%m"),
                    "orders": row["orders"] or 0,
                    "revenue": f"{int(row['revenue'] or 0):,}",
                }
            )

        status_counts = dict(
            queryset.values("status").annotate(count=Count("id")).values_list("status", "count")
        )
        status_rows = [
            {
                "label": label,
                "count": status_counts.get(code, 0),
            }
            for code, label in Order.Status.choices
        ]

        return {
            "total_orders": total_orders,
            "paid_orders": order_stats["paid_orders"] or 0,
            "cancelled_orders": cancelled_orders,
            "cancellation_rate": cancellation_rate,
            "total_revenue": f"{int(total_revenue):,}",
            "paid_revenue": f"{int(paid_revenue):,}",
            "delivered_revenue": f"{int(delivered_revenue):,}",
            "revenue_today": f"{int(revenue_today):,}",
            "revenue_month": f"{int(revenue_month):,}",
            "avg_order_value": f"{avg_order_value:,}",
            "order_status_rows": status_rows,
            "order_payment_rows": payment_rows,
            "order_daily_rows": daily_rows,
        }

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(self._quick_links_context())
        response = super().changelist_view(request, extra_context=extra_context)
        return response

    def stats_view(self, request):
        base_qs = self.get_queryset(request)
        analytics = self._build_analytics_context(base_qs)
        context = {
            **self.admin_site.each_context(request),
            **self._quick_links_context(),
            "opts": self.model._meta,
            "title": "Thống kê doanh thu đơn hàng",
            "order_kpis": {
                "total_orders": analytics["total_orders"],
                "paid_orders": analytics["paid_orders"],
                "cancelled_orders": analytics["cancelled_orders"],
                "cancellation_rate": analytics["cancellation_rate"],
                "total_revenue": analytics["total_revenue"],
                "paid_revenue": analytics["paid_revenue"],
                "delivered_revenue": analytics["delivered_revenue"],
                "revenue_today": analytics["revenue_today"],
                "revenue_month": analytics["revenue_month"],
                "avg_order_value": analytics["avg_order_value"],
            },
            "order_status_rows": analytics["order_status_rows"],
            "order_payment_rows": analytics["order_payment_rows"],
            "order_daily_rows": analytics["order_daily_rows"],
        }
        return TemplateResponse(request, "admin/orders/order/stats.html", context)
