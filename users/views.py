from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages

from .decorators import admin_required
from .forms import UserCreateForm, UserRoleForm
from .models import UserProfile


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
    return redirect("login")


def redirect_by_role(user):
    """Helper function to handle role-based redirection."""
    if hasattr(user, "profile"):
        role = user.profile.role
        if role == "ADMIN":
            return redirect("admin_dashboard")
        elif role == "MANAGER":
            return redirect("manager_dashboard")

    # Default fallback for cashiers
    return redirect("sales_dashboard")

# ---------------------------------------------------------------------------
# User & role management — admin only. (FR-36 — Role-Based Access)
# ---------------------------------------------------------------------------

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
            messages.success(request, "User created.")
            return redirect("user_list")
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
            messages.success(request, f"Updated role for {profile.user.username}.")
            return redirect("user_list")
    else:
        form = UserRoleForm(instance=profile)
    return render(request, "user_role_form.html", {"form": form, "profile": profile})


@admin_required
def user_toggle_active(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == "POST":
        if profile.user == request.user:
            messages.error(request, "You can't deactivate your own account.")
        else:
            profile.user.is_active = not profile.user.is_active
            profile.user.save()
    return redirect("user_list")
