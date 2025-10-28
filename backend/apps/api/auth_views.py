from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.accounts.models import UserRole

class WhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": getattr(user, "role", None),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "permissions": {
                "can_edit_teams": user.role in [UserRole.ADMIN],
                "can_edit_staff": user.role in [UserRole.ADMIN],
                "can_edit_players": user.role in [UserRole.ADMIN],
                "can_edit_heroes": user.role in [UserRole.ADMIN],
                "can_edit_tournaments": user.role in [UserRole.ADMIN],
                "can_edit_stages": user.role in [UserRole.ADMIN],
                "can_edit_series": user.role in [UserRole.ADMIN, UserRole.MODERATOR],
                "can_edit_games": user.role in [UserRole.ADMIN, UserRole.MODERATOR],
                "can_view_admin": bool(user.is_staff or user.is_superuser),
            }
        }, status=status.HTTP_200_OK)