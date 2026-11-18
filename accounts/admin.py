from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Menu, Role, RoleMenu, User


class RoleMenuInline(admin.TabularInline):
    model = RoleMenu
    extra = 1


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "real_name", "role", "department", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("扩展信息", {"fields": ("real_name", "phone", "department", "role")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    inlines = [RoleMenuInline]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "group_name", "url_name", "sort", "is_active")
    list_filter = ("group_name", "is_active")
