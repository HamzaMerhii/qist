from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


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