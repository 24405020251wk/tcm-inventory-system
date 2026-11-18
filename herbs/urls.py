from django.urls import path

from . import views

app_name = "herbs"

urlpatterns = [
    path("", views.herb_list, name="list"),
    path("create/", views.herb_form, name="create"),
    path("export/", views.herb_export, name="export"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_form, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("<int:pk>/", views.herb_detail, name="detail"),
    path("<int:pk>/edit/", views.herb_form, name="edit"),
    path("<int:pk>/delete/", views.herb_delete, name="delete"),
]
