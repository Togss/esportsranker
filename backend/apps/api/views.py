import rest_framework.filters as filters

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Q
from apps.teams.models import Team
from apps.teams.serializers import TeamSerializer
from apps.teams import selectors as team_selectors
from apps.players.models import Player
from apps.players.serializers import PlayerSerializer
from apps.competitions import selectors as comp_selectors
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
from apps.staff.models import Staff
from apps.staff.serializers import StaffSerializer
from apps.staff import selectors as staff_selectors
from apps.heroes import selectors as hero_selectors
from apps.heroes.models import Hero
from apps.heroes.serializers import HeroSerializer
from apps.api.permissions import (
    PublicRead_AdminOrModeratorWrite_NoDelete,
    IsAdminOnly,
    PublicRead_AdminWriteOnly,
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
    permission_classes = [PublicRead_AdminWriteOnly]

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

    def get_queryset(self):
        query = self.request.query_params.get("search")
        region = self.request.query_params.get("region")
        is_active_raw = self.request.query_params.get("is_active")

        if is_active_raw is None:
            is_active = None
        else:
            is_active = is_active_raw.lower() in ["1", "true", "t", "yes", "y"]

        return team_selectors.search_teams(
            query=query,
            region=region,
            is_active=is_active
        )


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Players.
    /api/v1/players/       → list active players
    /api/v1/players/<id>/  → player details with memberships
    """
    queryset = Player.objects.filter(is_active=True).select_related().prefetch_related("memberships__team")
    serializer_class = PlayerSerializer
    permission_classes = [PublicRead_AdminWriteOnly]

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

    def search_players(
        query: str | None = None,
        role: str | None = None,
        nationality: str | None = None,
        active_only: bool | None = None,
    ):
        qs = Player.objects.all()

        # fuzzy search by IGN or full name (SluggedModel.name)
        if query:
            qs = qs.filter(
                Q(ign__icontains=query)
                | Q(name__icontains=query)
            )

        # filter by role
        if role:
            qs = qs.filter(role=role)

        # nationality is stored as uppercase ISO alpha-2
        if nationality:
            qs = qs.filter(nationality__iexact=nationality)

        # active_only -> is_active
        if active_only is not None:
            qs = qs.filter(is_active=active_only)

        # We know Player.Meta.ordering = ['ign']
        # Prefetch memberships so serializers / views can access roster info without N+1 queries
        qs = qs.prefetch_related(
            "memberships__team",
        ).only(
            "id",
            "ign",
            "name",
            "slug",
            "role",
            "nationality",
            "is_active",
            "photo",
            "created_at",
            "updated_at",
        )

        return qs

class HeroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Heroes.
    /api/v1/heroes/       → list of heroes
    /api/v1/heroes/<id>/  → hero details
    """
    queryset = Hero.objects.all().order_by("name")
    serializer_class = HeroSerializer
    permission_classes = [PublicRead_AdminWriteOnly]

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

    def get_queryset(self):
        query = self.request.query_params.get("search")
        hero_class = self.request.query_params.get("hero_class")

        return hero_selectors.search_heroes(
            query=query,
            hero_class=hero_class
        )


class StaffViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for Staff.
    /api/v1/staff/       → list active staff members
    /api/v1/staff/<id>/  → staff member details with memberships
    """
    queryset = Staff.objects.filter(is_active=True).select_related().prefetch_related("memberships__team")
    serializer_class = StaffSerializer
    permission_classes = [PublicRead_AdminWriteOnly]

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

    def get_queryset(self):
        query = self.request.query_params.get("search")
        role = self.request.query_params.get("primary_role")
        nationality = self.request.query_params.get("nationality")

        raw_active = self.request.query_params.get("active_only")
        if raw_active is None:
            active_only = None
        else:
            active_only = raw_active.lower() in ["1", "true", "t", "yes", "y"]

        return staff_selectors.search_staff(
            query=query,
            role=role,
            nationality=nationality,
            active_only=active_only
        )


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
    permission_classes = [PublicRead_AdminWriteOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["region", "tier", "status"]
    ordering_fields = ["start_date", "end_date", "tier"]
    search_fields = ["name", "slug"]
    pagination_class = None  # Disable pagination for tournaments

    def get_queryset(self):
        qs = comp_selectors.get_active_tournaments()

        region = self.request.query_params.get("region")
        tier = self.request.query_params.get("tier")
        status = self.request.query_params.get("status")

        if region:
            qs = qs.filter(region=region)
        if tier:
            qs = qs.filter(tier=tier)
        if status:
            qs = qs.filter(status=status)
        return qs


class StageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stage.objects.select_related("tournament").order_by("order")
    serializer_class = StageSerializer
    permission_classes = [PublicRead_AdminWriteOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["tournament", "stage_type", "status"]
    ordering_fields = ["order", "start_date"]
    search_fields = ["variant"]


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Series.objects.select_related("tournament", "stage", "team1", "team2", "winner")
    serializer_class = SeriesSerializer
    permission_classes = [PublicRead_AdminWriteOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["tournament", "stage", "winner"]
    ordering_fields = ["scheduled_date"]
    search_fields = ["team1__short_name", "team2__short_name"]


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.select_related("series", "blue_side", "red_side", "winner")
    serializer_class = GameSerializer
    permission_classes = [PublicRead_AdminOrModeratorWrite_NoDelete]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["series", "winner"]
    ordering_fields = ["game_no", "duration"]


class TeamGameStatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamGameStat.objects.select_related("game", "team")
    serializer_class = TeamGameStatSerializer
    permission_classes = [PublicRead_AdminOrModeratorWrite_NoDelete]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["team", "game__series", "side"]
    ordering_fields = ["gold", "score"]


class PlayerGameStatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlayerGameStat.objects.select_related("game", "player", "team", "hero")
    serializer_class = PlayerGameStatSerializer
    permission_classes = [PublicRead_AdminOrModeratorWrite_NoDelete]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["player", "team", "hero", "role", "is_MVP"]
    ordering_fields = ["k", "d", "a", "gold", "dmg_dealt", "dmg_taken"]


class GameDraftActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameDraftAction.objects.select_related("game", "hero", "team", "player")
    serializer_class = GameDraftActionSerializer
    permission_classes = [PublicRead_AdminOrModeratorWrite_NoDelete]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["game", "side", "action"]
    ordering_fields = ["order"]