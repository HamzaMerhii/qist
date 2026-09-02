from django.urls import path
from .views import login_view, logout_view, user_list, user_create, user_edit_role, user_toggle_active

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/", user_list, name="user_list"),
    path("users/new/", user_create, name="user_create"),
    path("users/<int:pk>/role/", user_edit_role, name="user_edit_role"),
    path("users/<int:pk>/toggle-active/", user_toggle_active, name="user_toggle_active"),
]
