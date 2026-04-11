from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tags", views.TagViewSet, basename="tag")
router.register("suppliers", views.SupplierViewSet, basename="supplier")
router.register("products", views.ProductViewSet, basename="product")
router.register("stock-movements", views.StockMovementViewSet, basename="stock-movement")

urlpatterns = [
    path("", include(router.urls)),
    path("stats/", views.InventoryStatsView.as_view(), name="inventory-stats"),
    path("internal/reserve-stock/", views.ReserveStockView.as_view(), name="inventory-reserve-stock"),
    path("internal/release-stock/", views.ReleaseStockView.as_view(), name="inventory-release-stock"),
]
