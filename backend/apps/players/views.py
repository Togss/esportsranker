from django.db.models import OuterRef, Subquery, Q, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.players.models import Player, PlayerMembership
from apps.teams.models import Team
from .serializers import PlayerSerializer

class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public, read-only endpoint for Players with current-team annotation.
    """
    serializer_class = PlayerSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "nationality", "is_active"]
    search_fields = ["ign", "name", "slug"]
    ordering_fields = ["ign", "name", "created_at", "updated_at"]
    ordering = ["ign"]

    def get_queryset(self):
        qs = Player.objects.all().only(
            "id", "ign", "name", "slug", "role", "nationality", "date_of_birth",
            "photo", "achievements", "x", "facebook", "youtube", "instagram",
            "is_active", "created_at", "updated_at"
        )

        # Subquery to find active membership "today"
        from django.utils import timezone
        today = timezone.localdate()
        active_memberships = PlayerMembership.objects.filter(
            player=OuterRef("pk"),
            start_date__lte=today
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).order_by("-start_date")

        # Subqueries to pull Team fields for the active membership (if any)
        current_team_id_sq = active_memberships.values("team")[:1]
        team_base = Team.objects.filter(pk=Subquery(current_team_id_sq))
        current_team_name_sq = team_base.values("name")[:1]
        current_team_short_sq = team_base.values("short_name")[:1]
        current_team_slug_sq = team_base.values("slug")[:1]

        return qs.annotate(
            _current_team_id=Subquery(current_team_id_sq),
            _current_team_name=Subquery(current_team_name_sq),
            _current_team_short_name=Subquery(current_team_short_sq),
            _current_team_slug=Subquery(current_team_slug_sq),
        )