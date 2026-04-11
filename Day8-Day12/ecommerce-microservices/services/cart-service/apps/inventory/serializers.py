"""
Inventory Serializers — Day 9: DRF Serializers
Demo: ModelSerializer, nested, validation, read_only fields
"""
from rest_framework import serializers
from .models import Category, Tag, Supplier, Product, StockMovement


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "is_active", "product_count"]
        read_only_fields = ["slug"]

    def get_product_count(self, obj):
        return obj.products.filter(status="active").count()


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_name", "email", "phone", "address", "is_active"]


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer gọn cho list view"""
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "sku", "price", "stock",
            "status", "is_featured", "is_low_stock", "profit_margin",
            "category_name", "tags", "image_url", "created_at"
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer đầy đủ cho detail/create/update"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source="supplier", write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, source="tags", write_only=True, required=False
    )
    is_low_stock = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "sku", "description", "price", "cost_price",
            "stock", "min_stock", "status", "is_featured", "is_low_stock", "profit_margin",
            "category", "category_id", "supplier", "supplier_id",
            "tags", "tag_ids", "image", "image_url", "created_at", "updated_at"
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Giá bán phải lớn hơn 0.")
        return value

    def validate(self, attrs):
        cost = attrs.get("cost_price", 0)
        price = attrs.get("price", 0)
        if cost and price and cost > price:
            raise serializers.ValidationError("Giá vốn không được lớn hơn giá bán.")
        return attrs


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_name", "movement_type",
            "quantity", "note", "created_by", "created_by_name", "created_at"
        ]
        read_only_fields = ["created_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class InventoryStatsSerializer(serializers.Serializer):
    """ORM aggregate stats — demo annotate"""
    total_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=0)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    category_count = serializers.IntegerField()
    supplier_count = serializers.IntegerField()
