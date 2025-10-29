from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.accounts.models import UserRole


class PublicRead_AdminWriteOnly(BasePermission):
    """
    SAFE (GET/HEAD/OPTIONS):
        - allowed to ANYONE (public)
    UNSAFE (POST/PUT/PATCH/DELETE):
        - only allowed to Admin
    """
    def has_permission(self, request, view):
        method = request.method.upper()

        if method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)
        return role == UserRole.ADMIN


class PublicRead_AdminOrModeratorWrite_NoDelete(BasePermission):
    """
    SAFE (GET/HEAD/OPTIONS):
        - allowed to ANYONE (public)
    POST/PUT/PATCH:
        - allowed to Admin and Moderator
    DELETE:
        - allowed to Admin only
    """
    def has_permission(self, request, view):
        method = request.method.upper()

        if method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)

        if method == "DELETE":
            return role == UserRole.ADMIN

        if method in ["POST", "PUT", "PATCH"]:
            return role in [UserRole.ADMIN, UserRole.MODERATOR]

        return False


class IsAdminOnly(BasePermission):
    """Only Admin can do anything (even read)."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == UserRole.ADMIN
        )