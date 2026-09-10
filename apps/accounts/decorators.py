"""Function-view equivalents of the role mixins.

Usage::

    @editor_required
    def approve_article(request, pk): ...
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .roles import (
    ADMIN_ROLES,
    CONTRIBUTOR_ROLES,
    EDITORIAL_ROLES,
)


def _role_required(allowed_roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to view this page."
                )
            return view_func(request, *args, **kwargs)

        wrapper.__wrapped__ = view_func
        wrapper.__name__ = getattr(view_func, "__name__", "wrapped")
        return wrapper

    return decorator


contributor_required = _role_required(CONTRIBUTOR_ROLES)
editor_required = _role_required(EDITORIAL_ROLES)
admin_required = _role_required(ADMIN_ROLES)
