"""Custom DRF permissions for the newspaper API."""

from rest_framework import permissions

from apps.accounts.roles import (
    CONTRIBUTOR_ROLES,
    EDITORIAL_ROLES,
)


class IsContributor(permissions.BasePermission):
    """Only student/faculty/editor/admin roles may write articles."""

    message = "Your role cannot submit articles."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in CONTRIBUTOR_ROLES
        )


class IsAuthorOrEditor(permissions.BasePermission):
    """Object-level: the author, an editor or an admin may edit/delete."""

    message = "You may only modify your own articles."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        author = getattr(obj, "author", None) or getattr(obj, "user", None)
        return author == user or user.role in EDITORIAL_ROLES or \
            user.is_superuser


class IsEditorOrAdmin(permissions.BasePermission):
    message = "Editor or admin role required."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in EDITORIAL_ROLES
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated
            and (obj.user == user or user.role in EDITORIAL_ROLES)
        )


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.is_admin_role
        )
