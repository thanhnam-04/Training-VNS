from django.contrib import admin
from django.urls import path

from config.health import health_view

admin.site.site_header = "ShopVNS Admin"
admin.site.site_title = "ShopVNS Admin Portal"
admin.site.index_title = "System Administration"

urlpatterns = [
    path("health/", health_view, name="health"),
    path("admin/", admin.site.urls),
]
