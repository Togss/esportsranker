import rest_framework.filters as filters

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.response import Response
from apps.teams.models import Team
from apps.teams.serializers import TeamSerializer
from apps.players.models import Player
from apps.players.serializers import PlayerSerializer
from apps.competitions.models import (
    Tournament,
    Stage,
    Series,
    Game,
    TeamGameStat,
    PlayerGameStat,
    GameDraftAction
)
from apps.competitions.serializers import (
    TournamentSerializer,
    StageSerializer,
    SeriesSerializer,
    GameSerializer,
    TeamGameStatSerializer,
    PlayerGameStatSerializer,
    GameDraftActionSerializer
)


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Teams.
    Endpoints:
        /api/v1/teams/          → list of active teams
        /api/v1/teams/<id>/     → detailed view of a specific team
    """
    queryset = Team.objects.filter(is_active=True).order_by("short_name")
    serializer_class = TeamSerializer

    # Enable filters, ordering, and search
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "region",
        "is_active",
        "founded_year",
    ]
    ordering_fields = [
        "short_name",
        "region",
        "founded_year",
    ]
    search_fields = [
        "name",
        "short_name",
    ]


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Players.
    /api/v1/players/       → list active players
    /api/v1/players/<id>/  → player details with memberships
    """
    queryset = Player.objects.filter(is_active=True).select_related().prefetch_related("memberships__team")
    serializer_class = PlayerSerializer

    # Enable filters, ordering, and search
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "role",
        "nationality",
        "is_active",
    ]
    ordering_fields = [
        "ign",
        "role",
        "nationality",
        "created_at",
    ]
    search_fields = [
        "ign",
        "name",
        "slug",
    ]

class HeroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Heroes.
    /api/v1/heroes/       → list of heroes
    /api/v1/heroes/<id>/  → hero details
    """
    from apps.heroes.models import Hero
    from apps.heroes.serializers import HeroSerializer

    queryset = Hero.objects.all().order_by("name")
    serializer_class = HeroSerializer

    # Enable filters, ordering, and search
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "primary_class",
        "secondary_class",
    ]
    ordering_fields = [
        "name",
        "primary_class",
        "secondary_class",
        "created_at",
    ]
    search_fields = [
        "name",
        "slug",
    ]

class StaffViewSet(viewsets.ReadOnlyModelViewSet):
    from apps.staff.models import Staff
    from apps.staff.serializers import StaffSerializer
    """
    Public read-only API for Staff.
    /api/v1/staff/       → list active staff members
    /api/v1/staff/<id>/  → staff member details with memberships
    """
    queryset = Staff.objects.filter(is_active=True).select_related().prefetch_related("memberships__team")
    serializer_class = StaffSerializer

    # Enable filters, ordering, and search
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "primary_role",
        "nationality",
        "is_active",
    ]
    ordering_fields = [
        "handle",
        "primary_role",
        "nationality",
        "created_at",
    ]
    search_fields = [
        "handle",
        "slug",
    ]


class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Tournament.objects.all()
        .prefetch_related(
            "stages__series__games__team_stats",
            "stages__series__games__player_stats",
            "stages__series__games__draft_actions",
        )
        .order_by("-start_date")
    )
    serializer_class = TournamentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["region", "tier", "status"]
    ordering_fields = ["start_date", "end_date", "tier"]
    search_fields = ["name", "slug"]
    pagination_class = None  # Disable pagination for tournaments


class StageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stage.objects.select_related("tournament").order_by("order")
    serializer_class = StageSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["tournament", "stage_type", "status"]
    ordering_fields = ["order", "start_date"]
    search_fields = ["variant"]


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Series.objects.select_related("tournament", "stage", "team1", "team2", "winner")
    serializer_class = SeriesSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["tournament", "stage", "winner"]
    ordering_fields = ["scheduled_date"]
    search_fields = ["team1__short_name", "team2__short_name"]


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.select_related("series", "blue_side", "red_side", "winner")
    serializer_class = GameSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["series", "winner"]
    ordering_fields = ["game_no", "duration"]


class TeamGameStatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamGameStat.objects.select_related("game", "team")
    serializer_class = TeamGameStatSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["team", "game__series", "side"]
    ordering_fields = ["gold", "score"]


class PlayerGameStatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlayerGameStat.objects.select_related("game", "player", "team", "hero")
    serializer_class = PlayerGameStatSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["player", "team", "hero", "role", "is_MVP"]
    ordering_fields = ["k", "d", "a", "gold", "dmg_dealt", "dmg_taken"]


class GameDraftActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameDraftAction.objects.select_related("game", "hero", "team", "player")
    serializer_class = GameDraftActionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["game", "side", "action"]
    ordering_fields = ["order"]