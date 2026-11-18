from django.urls import path

from . import views

app_name = "inbound"

urlpatterns = [
    path("", views.inbound_list, name="list"),
    path("create/", views.inbound_form, name="create"),
    path("export/", views.inbound_export, name="export"),
    path("<int:pk>/", views.inbound_detail, name="detail"),
    path("<int:pk>/edit/", views.inbound_form, name="edit"),
    path("<int:pk>/confirm/", views.inbound_confirm, name="confirm"),
    path("<int:pk>/cancel/", views.inbound_cancel, name="cancel"),
    path("<int:pk>/print/", views.inbound_print, name="print"),
]
