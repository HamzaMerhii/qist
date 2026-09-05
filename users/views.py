
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from .models import UserProfile
from .forms import UserCreateForm, UserRoleForm


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (hasattr(request.user, "profile") and request.user.profile.role == "ADMIN"):
            messages.error(request, "You don't have permission to access that page.")
            return redirect("dashboards:sales_dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped


def login_view(request):
    # Redirect if the user is already logged in
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect_by_role(user)
        
        # If authentication or form validation fails
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    # Change "users/login.html" to "login.html"
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("users:login")


def redirect_by_role(user):
    """Helper function to handle role-based redirection."""
    if hasattr(user, "profile") and user.profile.role == "ADMIN":
        return redirect("dashboards:admin_dashboard")

    # Everyone else (sales/cashier) goes to the sales dashboard
    return redirect("dashboards:sales_dashboard")


@admin_required
def user_list(request):
    profiles = UserProfile.objects.select_related("user").order_by("user__username")
    return render(request, "user_list.html", {"profiles": profiles})


@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("users:user_list")
    else:
        form = UserCreateForm()

    return render(request, "user_form.html", {"form": form})


@admin_required
def user_edit_role(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == "POST":
        form = UserRoleForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Role updated for {profile.user.username}.")
            return redirect("users:user_list")
    else:
        form = UserRoleForm(instance=profile)

    return render(request, "user_role_form.html", {"form": form, "profile": profile})


@admin_required
def user_toggle_active(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == "POST" and profile.user != request.user:
        profile.user.is_active = not profile.user.is_active
        profile.user.save()
        messages.success(
            request,
            f"{profile.user.username} {'activated' if profile.user.is_active else 'deactivated'}.",
        )
    return redirect("users:user_list")