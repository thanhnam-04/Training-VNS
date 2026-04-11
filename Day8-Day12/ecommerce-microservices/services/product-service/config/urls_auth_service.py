from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from config.health import health_view

urlpatterns = [
    path("health/", health_view, name="health"),
    path("api/auth/", include("apps.users.urls")),
    path("admin/", admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
