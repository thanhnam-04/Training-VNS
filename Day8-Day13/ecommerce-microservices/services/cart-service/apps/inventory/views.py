"""
Inventory Views — Day 9: ViewSets, GenericViews, Permissions
Demo: ModelViewSet, GenericAPIView, IsAdminUser, custom action
"""
from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField
from django.db import transaction
from .models import Category, Tag, Supplier, Product, StockMovement
from .serializers import (
    CategorySerializer, TagSerializer, SupplierSerializer,
    ProductListSerializer, ProductDetailSerializer,
    StockMovementSerializer, InventoryStatsSerializer
)
import django_filters


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["category", "supplier", "status", "is_featured"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD danh mục — ai cũng xem, chỉ admin mới sửa"""
    queryset = Category.objects.annotate(product_count=Count("products")).filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "contact_name"]


class ProductViewSet(viewsets.ModelViewSet):
    """
    Day 9: ModelViewSet với custom actions
    Day 10: select_related + prefetch_related để tối ưu query
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["price", "stock", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Day 10: select_related + prefetch_related tránh N+1
        return Product.objects.select_related(
            "category", "supplier"
        ).prefetch_related("tags").all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=["get"], url_path="featured")
    def featured(self, request):
        """GET /api/inventory/products/featured/ — Sản phẩm nổi bật"""
        qs = self.get_queryset().filter(is_featured=True, status="active")[:8]
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="low-stock",
            permission_classes=[permissions.IsAdminUser])
    def low_stock(self, request):
        """GET /api/inventory/products/low-stock/ — Sản phẩm sắp hết hàng"""
        qs = self.get_queryset().filter(stock__lte=F("min_stock"), stock__gt=0)
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="upload-image",
            permission_classes=[permissions.IsAdminUser])
    def upload_image(self, request, pk=None):
        """POST /api/inventory/products/{id}/upload-image/"""
        product = self.get_object()
        if "image" not in request.FILES:
            return Response({"error": "Chưa có file ảnh."}, status=status.HTTP_400_BAD_REQUEST)
        product.image = request.FILES["image"]
        product.save()
        return Response(ProductDetailSerializer(product, context={"request": request}).data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """Biến động kho — chỉ admin"""
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "movement_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return StockMovement.objects.select_related("product", "created_by").all()


class InventoryStatsView(generics.GenericAPIView):
    """
    GET /api/inventory/stats/ — Thống kê tổng hợp kho hàng
    Day 8: ORM annotate + aggregate
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper

        stock_value = Product.objects.aggregate(
            total=Sum(
                ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())
            )
        )["total"] or 0

        stats = {
            "total_products": Product.objects.count(),
            "total_stock_value": stock_value,
            "low_stock_count": Product.objects.filter(
                stock__lte=F("min_stock"), stock__gt=0
            ).count(),
            "out_of_stock_count": Product.objects.filter(stock=0).count(),
            "category_count": Category.objects.filter(is_active=True).count(),
            "supplier_count": Supplier.objects.filter(is_active=True).count(),
        }
        return Response(stats)


class ReserveStockView(APIView):
    """Internal API: Reserve stock atomically for checkout."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        items = request.data.get("items", [])
        if not isinstance(items, list) or not items:
            return Response({"error": "items is required."}, status=status.HTTP_400_BAD_REQUEST)

        quantities: dict[int, int] = {}
        for item in items:
            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity"))
            except (TypeError, ValueError):
                return Response({"error": "Invalid reserve payload."}, status=status.HTTP_400_BAD_REQUEST)

            if quantity <= 0:
                return Response({"error": "Quantity must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
            quantities[product_id] = quantities.get(product_id, 0) + quantity

        products = Product.objects.select_for_update().filter(pk__in=list(quantities.keys()))
        product_map = {product.id: product for product in products}

        reserved = []
        for product_id, quantity in quantities.items():
            product = product_map.get(product_id)
            if not product:
                return Response({"error": f"Sản phẩm #{product_id} không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)
            if product.stock < quantity:
                return Response(
                    {"error": f"Sản phẩm '{product.name}' chỉ còn {product.stock} cái."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.stock -= quantity
            if product.stock == 0:
                product.status = Product.Status.OUT_OF_STOCK
            product.save(update_fields=["stock", "status", "updated_at"])
            reserved.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "unit_price": str(product.price),
                    "quantity": quantity,
                }
            )

        return Response({"reserved": reserved}, status=status.HTTP_200_OK)


class ReleaseStockView(APIView):
    """Internal API: Compensation endpoint for failed checkout."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        items = request.data.get("items", [])
        if not isinstance(items, list) or not items:
            return Response({"restored": 0}, status=status.HTTP_200_OK)

        quantities: dict[int, int] = {}
        for item in items:
            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity"))
            except (TypeError, ValueError):
                continue
            if quantity > 0:
                quantities[product_id] = quantities.get(product_id, 0) + quantity

        if not quantities:
            return Response({"restored": 0}, status=status.HTTP_200_OK)

        products = Product.objects.select_for_update().filter(pk__in=list(quantities.keys()))
        restored = 0
        for product in products:
            quantity = quantities.get(product.id, 0)
            if quantity <= 0:
                continue
            product.stock += quantity
            if product.stock > 0 and product.status == Product.Status.OUT_OF_STOCK:
                product.status = Product.Status.ACTIVE
            product.save(update_fields=["stock", "status", "updated_at"])
            restored += 1

        return Response({"restored": restored}, status=status.HTTP_200_OK)
