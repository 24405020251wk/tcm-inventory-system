from django.contrib import admin

from .models import Herb, HerbCategory


@admin.register(HerbCategory)
class HerbCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort")


@admin.register(Herb)
class HerbAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "spec", "unit", "min_stock",
                    "price", "status")
    list_filter = ("category", "status")
    search_fields = ("code", "name", "pinyin")
