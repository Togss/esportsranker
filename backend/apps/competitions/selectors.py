from datetime import timedelta
from django.utils import timezone
from django.db.models import Prefetch, Q, Count, F

from .models import (
    Tournament,
    Stage,
    Series,
    Game,
    TeamGameStat,
    PlayerGameStat,
    TournamentTeam,
)


def get_upcoming_series(limit=20):
    """
    Return the next N scheduled Series across all tournaments,
    ordered soonest first.

    Only future (or very recent ongoing) series are returned.
    """
    now = timezone.now()

    qs = (
        Series.objects.select_related(
            "tournament",
            "stage",
            "team1",
            "team2",
            "winner",
        )
        .filter(scheduled_date__gte=now - timedelta(hours=2))
        .order_by("scheduled_date")[:limit]
    )

    return qs


def get_tournament_with_structure(tournament_id: int):
    """
    Get a Tournament and its stages and series in one go.

    Used for: tournament page in frontend, admin previews, etc.
    This is read-only; DO NOT mutate in here.
    """

    # Prefetch Series under each Stage
    series_prefetch = Prefetch(
        "series",
        queryset=Series.objects.select_related(
            "team1",
            "team2",
            "winner",
        ).order_by("-scheduled_date"),
    )

    # Prefetch Stages under Tournament with their Series
    stage_prefetch = Prefetch(
        "stages",
        queryset=Stage.objects.prefetch_related(series_prefetch).order_by("order", "start_date"),
    )

    # Prefetch registered teams
    teams_prefetch = Prefetch(
        "tournamentteam_set",
        queryset=TournamentTeam.objects.select_related("team").order_by("seed", "team__short_name"),
    )

    return (
        Tournament.objects
        .filter(pk=tournament_id)
        .prefetch_related(stage_prefetch, teams_prefetch)
        .first()
    )


def get_series_detail(series_id: int):
    """
    Return a single Series with:
    - tournament
    - stage
    - both teams
    - all games with stats + draft
    This will feed your match detail page later.
    """

    games_prefetch = Prefetch(
        "games",
        queryset=Game.objects.select_related(
            "blue_side",
            "red_side",
            "winner",
        )
        .prefetch_related(
            # per-team totals
            Prefetch(
                "team_stats",
                queryset=TeamGameStat.objects.select_related(
                    "team",
                ).order_by("side"),
            ),
            # per-player stats
            Prefetch(
                "player_stats",
                queryset=PlayerGameStat.objects.select_related(
                    "player",
                    "team",
                    "team_stat",
                ).order_by(
                    "team_stat__side",
                    "player__ign",
                ),
            ),
            # draft picks / bans
            "gamedraftaction_set",
        )
        .order_by("game_no"),
    )

    return (
        Series.objects
        .select_related(
            "tournament",
            "stage",
            "team1",
            "team2",
            "winner",
        )
        .prefetch_related(games_prefetch)
        .filter(pk=series_id)
        .first()
    )


def get_stage_schedule(stage_id: int):
    """
    Get all series for a given Stage in chronological order.
    Helpful for rendering a stage page / bracket block.
    """

    return (
        Series.objects
        .select_related(
            "tournament",
            "stage",
            "team1",
            "team2",
            "winner",
        )
        .filter(stage_id=stage_id)
        .order_by("scheduled_date")
    )


def get_team_recent_series(team_id: int, limit=10):
    """
    Get a team's last N series (either as team1 or team2),
    newest first.
    Will be used in the Team Profile page 'Recent Results' widget.
    """

    return (
        Series.objects
        .select_related(
            "tournament",
            "stage",
            "team1",
            "team2",
            "winner",
        )
        .filter(
            Q(team1_id=team_id) | Q(team2_id=team_id)
        )
        .order_by("-scheduled_date")[:limit]
    )