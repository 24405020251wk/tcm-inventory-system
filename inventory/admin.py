from django.contrib import admin

from .models import StockLedger


@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ("created_at", "herb", "batch", "biz_type", "change_qty",
                    "after_qty", "ref_no", "operator")
    list_filter = ("biz_type", "created_at")
    search_fields = ("herb__name", "ref_no")
