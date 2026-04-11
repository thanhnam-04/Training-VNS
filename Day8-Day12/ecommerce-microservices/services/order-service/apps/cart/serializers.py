from rest_framework import serializers
from apps.inventory.serializers import ProductListSerializer
from apps.inventory.models import Product
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(status="active"),
        source="product", write_only=True
    )
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal", "added_at"]
        read_only_fields = ["id", "added_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total_items", "total_price", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        from apps.inventory.models import Product
        try:
            product = Product.objects.get(pk=value, status="active")
            if product.stock == 0:
                raise serializers.ValidationError("Sản phẩm đã hết hàng.")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Sản phẩm không tồn tại.")


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
