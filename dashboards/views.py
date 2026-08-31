from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    return render(request, "admin.html")

@login_required
def manager_dashboard(request):
    return render(request, "manager.html")

@login_required
def sales_dashboard(request):
    return render(request, "sales.html")