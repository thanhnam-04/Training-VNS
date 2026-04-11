"""
Orders Views — Day 10: Checkout với quan hệ phức tạp
Day 11/12: Trigger Celery task gửi email sau khi checkout
"""
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from decimal import Decimal
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer, OrderStatusUpdateSerializer
from .service_clients import (
    ServiceClientError,
    clear_cart,
    fetch_cart_snapshot,
    release_stock,
    reserve_stock,
)
import logging

logger = logging.getLogger(__name__)


class CheckoutView(APIView):
    """POST /api/orders/checkout/ — Tạo đơn hàng từ giỏ hàng"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart_snapshot = fetch_cart_snapshot(request)
        except ServiceClientError as exc:
            return Response({"error": str(exc)}, status=exc.status_code)

        cart_items = cart_snapshot.get("items", [])

        if not cart_items:
            return Response({"error": "Giỏ hàng trống."}, status=status.HTTP_400_BAD_REQUEST)

        reserve_items = []
        for item in cart_items:
            product_id = item.get("product", {}).get("id")
            quantity = item.get("quantity", 0)
            if not product_id or quantity <= 0:
                return Response(
                    {"error": "Dữ liệu giỏ hàng không hợp lệ."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            reserve_items.append({"product_id": product_id, "quantity": quantity})

        try:
            reserved_items = reserve_stock(request, reserve_items)
        except ServiceClientError as exc:
            return Response({"error": str(exc)}, status=exc.status_code)

        subtotal = sum(Decimal(str(item["unit_price"])) * int(item["quantity"]) for item in reserved_items)
        shipping_fee = 30000
        total_amount = subtotal + shipping_fee

        try:
            order = Order.objects.create(
                user=request.user,
                shipping_name=serializer.validated_data["shipping_name"],
                shipping_phone=serializer.validated_data["shipping_phone"],
                shipping_address=serializer.validated_data["shipping_address"],
                payment_method=serializer.validated_data["payment_method"],
                note=serializer.validated_data.get("note", ""),
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
            )

            order_items = []
            for item in reserved_items:
                order_items.append(OrderItem(
                    order=order,
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    product_sku=item["product_sku"],
                    unit_price=item["unit_price"],
                    quantity=item["quantity"],
                ))

            OrderItem.objects.bulk_create(order_items)
        except Exception:
            release_stock(request, reserve_items)
            raise

        try:
            clear_cart(request)
        except ServiceClientError as exc:
            logger.warning(f"Cannot clear cart after checkout: {exc}")

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ — Lịch sử đơn hàng của user"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__product").order_by("-created_at")


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/{id}/ — Chi tiết đơn hàng"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__product")


class AdminOrderViewSet(viewsets.ModelViewSet):
    """Admin: quản lý tất cả đơn hàng"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Order.objects.select_related("user").prefetch_related(
            "items__product"
        ).order_by("-created_at")

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)
