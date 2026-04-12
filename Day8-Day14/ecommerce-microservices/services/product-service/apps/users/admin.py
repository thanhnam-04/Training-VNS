from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "get_full_name_display", "phone",
                    "is_staff", "is_verified", "is_active", "created_at"]
    list_filter = ["is_staff", "is_verified", "is_active", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name", "phone"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Thông tin cá nhân"), {"fields": ("first_name", "last_name", "phone", "avatar", "address")}),
        (_("Phân quyền"), {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions")}),
        (_("Thời gian"), {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "password1", "password2"),
        }),
    )

    @admin.display(description="Họ tên", ordering="first_name")
    def get_full_name_display(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else "—"
