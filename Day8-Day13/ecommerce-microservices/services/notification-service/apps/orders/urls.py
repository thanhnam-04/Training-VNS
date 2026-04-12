from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Admin ViewSet (quản lý tất cả đơn hàng)
admin_router = DefaultRouter()
admin_router.register("", views.AdminOrderViewSet, basename="admin-order")

urlpatterns = [
    # User-facing endpoints
    path("", views.OrderListView.as_view(), name="order-list"),
    path("checkout/", views.CheckoutView.as_view(), name="order-checkout"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),

    # Admin CRUD (IsAdminUser)  →  /api/orders/admin/
    path("admin/", include(admin_router.urls)),
]
