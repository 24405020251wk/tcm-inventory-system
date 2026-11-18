from django.urls import path

from . import views

app_name = "outbound"

urlpatterns = [
    path("", views.outbound_list, name="list"),
    path("create/", views.outbound_form, name="create"),
    path("export/", views.outbound_export, name="export"),
    path("<int:pk>/", views.outbound_detail, name="detail"),
    path("<int:pk>/edit/", views.outbound_form, name="edit"),
    path("<int:pk>/submit/", views.outbound_submit, name="submit"),
    path("<int:pk>/approve/", views.outbound_approve, name="approve"),
    path("<int:pk>/reject/", views.outbound_reject, name="reject"),
    path("<int:pk>/cancel/", views.outbound_cancel, name="cancel"),
    path("<int:pk>/print/", views.outbound_print, name="print"),
    path("<int:pk>/attachments/upload/", views.attachment_upload, name="attachment_upload"),
    path("<int:pk>/attachments/<int:att_id>/delete/", views.attachment_delete,
         name="attachment_delete"),
]
