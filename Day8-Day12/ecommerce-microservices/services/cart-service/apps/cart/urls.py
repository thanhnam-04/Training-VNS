from django.urls import path
from . import views

urlpatterns = [
    path("", views.CartView.as_view(), name="cart-detail"),
    path("add/", views.AddToCartView.as_view(), name="cart-add"),
    path("items/<int:item_id>/", views.UpdateCartItemView.as_view(), name="cart-item-update"),
    path("items/<int:item_id>/remove/", views.RemoveCartItemView.as_view(), name="cart-item-remove"),
    path("clear/", views.ClearCartView.as_view(), name="cart-clear"),
]
