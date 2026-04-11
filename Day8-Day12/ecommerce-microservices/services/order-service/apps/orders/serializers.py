from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "product_sku",
                  "unit_price", "quantity", "subtotal"]
        read_only_fields = ["product_name", "product_sku", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "user_email", "status", "status_display",
            "payment_method", "payment_display", "is_paid",
            "shipping_name", "shipping_phone", "shipping_address",
            "subtotal", "shipping_fee", "total_amount", "note",
            "items", "created_at", "updated_at"
        ]
        read_only_fields = [
            "order_number", "subtotal", "total_amount", "created_at", "updated_at"
        ]


class CheckoutSerializer(serializers.Serializer):
    """Tạo đơn hàng từ giỏ hàng"""
    shipping_name = serializers.CharField(max_length=100)
    shipping_phone = serializers.CharField(max_length=20)
    shipping_address = serializers.CharField()
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices,
                                              default=Order.PaymentMethod.COD)
    note = serializers.CharField(required=False, allow_blank=True)


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status", "is_paid"]
