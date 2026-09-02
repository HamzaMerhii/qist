from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """Require authentication and one of the supplied UserProfile roles."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = request.user

            # Django superusers retain full access even if a legacy profile has
            # not yet been assigned the ADMIN role.
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(user, "profile", None)
            if profile is None or profile.role not in allowed_roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return login_required(wrapped_view)

    return decorator
