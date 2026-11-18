from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("stock/", views.stock_list, name="stock"),
    path("stock/export/", views.stock_export, name="stock_export"),
    path("batches/", views.batch_list, name="batch_list"),
    path("stats/", views.stats, name="stats"),
    path("ledger/", views.ledger_list, name="ledger"),
    path("ledger/export/", views.ledger_export, name="ledger_export"),
    path("logs/", views.log_list, name="logs"),
]
