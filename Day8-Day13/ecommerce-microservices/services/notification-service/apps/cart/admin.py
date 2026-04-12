from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["product", "quantity", "subtotal", "added_at"]

    def subtotal(self, obj):
        return f"{obj.subtotal:,.0f} ₫"
    subtotal.short_description = "Thành tiền"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "total_items", "total_price_display", "updated_at"]
    readonly_fields = ["user", "created_at", "updated_at"]
    inlines = [CartItemInline]

    def total_price_display(self, obj):
        return f"{obj.total_price:,.0f} ₫"
    total_price_display.short_description = "Tổng tiền"
