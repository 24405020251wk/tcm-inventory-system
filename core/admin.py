from django.contrib import admin

from .models import OperationLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "module", "action", "target", "ip")
    list_filter = ("module", "created_at")
    search_fields = ("username", "action", "target")
    readonly_fields = ("created_at",)
