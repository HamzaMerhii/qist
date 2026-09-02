from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from accounts.forms import UserUpdateForm, UserCreationWithRoleForm


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


def admin_required(user):
    """Custom check to ensure user is active and has ADMIN role."""
    return user.is_authenticated and hasattr(user, "profile") and user.profile.role == "ADMIN"


@login_required
@user_passes_test(admin_required)
def user_list(request):
    users = User.objects.select_related("profile").order_by("-date_joined")
    return render(request, "user_list.html", {"users": users})


@login_required
@user_passes_test(admin_required)
def user_create(request):
    if request.method == "POST":
        form = UserCreationWithRoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New staff account created successfully.")
            return redirect("users:user_list")
    else:
        form = UserCreationWithRoleForm()

    return render(request, "user_form.html", {"form": form, "title": "Create User"})


@login_required
@user_passes_test(admin_required)
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            user_obj = form.save()
            user_obj.profile.role = form.cleaned_data["role"]
            user_obj.profile.save()
            messages.success(request, f"Updated profile for {user_obj.username}.")
            return redirect("users:user_list")
    else:
        form = UserUpdateForm(
            instance=user_obj, 
            initial={"role": user_obj.profile.role}
        )

    return render(
        request, 
        "user_form.html", 
        {"form": form, "title": f"Edit User: {user_obj.username}"}
    )



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