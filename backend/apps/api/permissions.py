from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.accounts.models import UserRole


class IsAdminOrReadOnly(BasePermission):
    """
    - Anyone authenticated can READ (GET, HEAD, OPTIONS).
    - Only Admins can WRITE (POST, PUT, PATCH, DELETE).
    Use this for high-trust objects like Tournament, Team, Player, Staff.
    """

    def has_permission(self, request, view):
        # Read-only methods are always fine for logged-in users
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write methods require ADMIN role
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == UserRole.ADMIN
        )


class CanEditMatches(BasePermission):
    """
    - Anyone authenticated can READ.
    - Admin OR Moderator can WRITE match-related data
      (Games, Series, TeamGameStat, PlayerGameStat, etc.)
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        user_role = getattr(request.user, "role", None)
        return (
            request.user
            and request.user.is_authenticated
            and user_role in [UserRole.ADMIN, UserRole.MODERATOR]
        )


class IsAdminOnly(BasePermission):
    """
    Full lock: only Admins can do anything, including read.
    You probably won't use this today, but it's handy for
    future maintenance endpoints, internal sync endpoints, etc.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == UserRole.ADMIN
        )