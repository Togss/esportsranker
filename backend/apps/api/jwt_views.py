from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from apps.accounts.models import UserRole


class EsportsTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Override the default serializer so we can attach user info in the response.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # You can also embed custom claims into the token itself if you want:
        token["role"] = getattr(user, "role", None)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # add extra top-level fields to response
        user = self.user
        data["user"] = {
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
            },
        }

        return data


class EsportsTokenObtainPairView(TokenObtainPairView):
    serializer_class = EsportsTokenObtainPairSerializer