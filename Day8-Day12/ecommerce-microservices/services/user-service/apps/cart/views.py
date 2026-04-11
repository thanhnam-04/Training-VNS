"""
Cart Views — Day 10: Relationships & Query Optimization
Demo: select_related, prefetch_related, get_or_create
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.inventory.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, UpdateCartItemSerializer


class CartView(generics.RetrieveAPIView):
    """GET /api/cart/ — Xem giỏ hàng của user hiện tại"""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Day 10: prefetch_related để tránh N+1
        cart, _ = Cart.objects.prefetch_related(
            "items__product__category",
            "items__product__tags",
        ).get_or_create(user=self.request.user)
        return cart


class AddToCartView(APIView):
    """POST /api/cart/add/ — Thêm sản phẩm vào giỏ"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(Product, pk=serializer.validated_data["product_id"])
        quantity = serializer.validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Reload với select_related
        cart = Cart.objects.prefetch_related(
            "items__product__category", "items__product__tags"
        ).get(user=request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    """PUT /api/cart/items/{id}/ — Cập nhật số lượng"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, item_id):
        cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item.quantity = serializer.validated_data["quantity"]
        cart_item.save()
        cart = Cart.objects.prefetch_related("items__product").get(user=request.user)
        return Response(CartSerializer(cart).data)


class RemoveCartItemView(APIView):
    """DELETE /api/cart/items/{id}/ — Xóa 1 sản phẩm khỏi giỏ"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        cart_item.delete()
        cart = Cart.objects.prefetch_related("items__product").get(user=request.user)
        return Response(CartSerializer(cart).data)


class ClearCartView(APIView):
    """DELETE /api/cart/clear/ — Xóa toàn bộ giỏ hàng"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.clear()
        return Response({"message": "Đã xóa giỏ hàng."})
