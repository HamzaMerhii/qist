from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.user_list, name="user_list"),
    path("create/", views.user_create, name="user_create"),
    path("<int:pk>/role/", views.user_edit_role, name="user_edit_role"),
    path("<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
]