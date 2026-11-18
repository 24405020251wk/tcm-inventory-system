from django.contrib import admin

from .models import Batch, InboundItem, InboundOrder


class InboundItemInline(admin.TabularInline):
    model = InboundItem
    extra = 0


@admin.register(InboundOrder)
class InboundOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "supplier", "inbound_date", "operator", "status")
    list_filter = ("status", "inbound_date")
    search_fields = ("order_no", "supplier")
    inlines = [InboundItemInline]


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_no", "herb", "remaining_quantity", "expiry_date",
                    "supplier", "status")
    list_filter = ("status",)
    search_fields = ("batch_no", "herb__name")
