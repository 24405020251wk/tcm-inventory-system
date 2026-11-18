from django.contrib import admin

from .models import OutboundItem, OutboundOrder


class OutboundItemInline(admin.TabularInline):
    model = OutboundItem
    extra = 0


@admin.register(OutboundOrder)
class OutboundOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "department", "applicant", "apply_date",
                    "status", "approver")
    list_filter = ("status", "apply_date")
    search_fields = ("order_no", "department", "purpose")
    inlines = [OutboundItemInline]
