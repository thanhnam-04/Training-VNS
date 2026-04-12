from django.urls import include, path

from config.health import health_view

urlpatterns = [
    path("health/", health_view, name="health"),
    path("api/inventory/", include("apps.inventory.urls")),
]
