from django.shortcuts import render

from accounts.models import UserProfile
from accounts.permissions import role_required

from .services import (
    get_admin_dashboard_context,
    get_cashier_dashboard_context,
    get_manager_dashboard_context,
)


@role_required(UserProfile.Role.ADMIN)
def admin_dashboard(request):
    return render(request, "admin.html", get_admin_dashboard_context())


@role_required(UserProfile.Role.ADMIN, UserProfile.Role.MANAGER)
def manager_dashboard(request):
    return render(request, "manager.html", get_manager_dashboard_context())


@role_required(
    UserProfile.Role.ADMIN,
    UserProfile.Role.MANAGER,
    UserProfile.Role.CASHIER,
)
def sales_dashboard(request):
    return render(request, "sales.html", get_cashier_dashboard_context())
