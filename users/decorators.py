from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def admin_required(view_func):
    """Restrict a view to users whose profile role is ADMIN. (FR-36 — Role-Based Access)"""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        role = getattr(getattr(request.user, "profile", None), "role", None)
        if role != "ADMIN":
            from .views import redirect_by_role
            messages.error(request, "You don't have permission to access that page.")
            return redirect_by_role(request.user)
        return view_func(request, *args, **kwargs)

    return _wrapped
