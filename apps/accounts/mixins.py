"""Reusable role-based access mixins for class-based views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .roles import (
    ADMIN_ROLES,
    CONTRIBUTOR_ROLES,
    EDITORIAL_ROLES,
    CustomUserRole,
    role_at_least,
)


class RoleRequiredMixin(LoginRequiredMixin):
    """Restrict a view to one or more ``CustomUserRole`` values.

    Usage::

        class MyView(RoleRequiredMixin, TemplateView):
            allowed_roles = (CustomUserRole.EDITOR, CustomUserRole.ADMIN)
            minimum_role = None  # alternative: role-level check
    """

    allowed_roles = None
    minimum_role = None
    raise_exception = True  # return 403 instead of redirecting to login

    def check_role(self, user):
        if self.allowed_roles is not None:
            return user.role in self.allowed_roles
        if self.minimum_role is not None:
            return role_at_least(user, self.minimum_role)
        return True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Anonymous users are redirected to the login page; only
            # authenticated-but-wrong-role users receive a 403.
            self.raise_exception = False
            return super().dispatch(request, *args, **kwargs)
        if not self.check_role(request.user):
            raise PermissionDenied("You do not have permission to view "
                                   "this page.")
        return super().dispatch(request, *args, **kwargs)


class ContributorRequiredMixin(RoleRequiredMixin):
    allowed_roles = CONTRIBUTOR_ROLES


class EditorRequiredMixin(RoleRequiredMixin):
    allowed_roles = EDITORIAL_ROLES
    minimum_role = CustomUserRole.EDITOR


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ADMIN_ROLES
    minimum_role = CustomUserRole.ADMIN
