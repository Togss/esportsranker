from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Team
from .serializers import TeamSerializer

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public, read-only endpoint for Teams.
    """
    queryset = Team.objects.all().only(
        "id", "name", "short_name", "slug", "region",
        "logo", "founded_year", "description", "achievements",
        "website", "x", "facebook", "youtube",
        "is_active", "created_at", "updated_at",
    )
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]

    # Basic filters/search/order for UI use
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["region", "is_active", "founded_year"]
    search_fields = ["name", "short_name", "slug"]
    ordering_fields = ["short_name", "founded_year", "created_at", "updated_at"]
    ordering = ["short_name"]