from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_form, name="user_create"),
    path("users/<int:pk>/edit/", views.user_form, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle, name="user_toggle"),
    path("users/<int:pk>/reset-password/", views.user_reset_password, name="user_reset_password"),
    path("roles/", views.role_list, name="role_list"),
    path("roles/create/", views.role_form, name="role_create"),
    path("roles/<int:pk>/edit/", views.role_form, name="role_edit"),
    path("roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("menus/", views.menu_list, name="menu_list"),
    path("menus/create/", views.menu_form, name="menu_create"),
    path("menus/<int:pk>/edit/", views.menu_form, name="menu_edit"),
]
