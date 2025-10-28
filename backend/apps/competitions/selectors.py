from datetime import timedelta
from django.utils import timezone
from django.db.models import Prefetch, Q

from .models import (
    Tournament,
    Stage,
    Series,
    Game,
    TeamGameStat,
    PlayerGameStat,
    TournamentTeam,
)


def get_upcoming_series(limit: int = 20):
    """
    Return the next N scheduled Series across all tournaments, ordered soonest first.
    We allow a small grace window (2h back) so just-started series still appear.

    Used for: homepage 'Upcoming / Live', moderator dashboard.
    """
    now = timezone.now()

    qs = (
        Series.objects
        .select_related(
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
    Load a specific Tournament in a fully nested way:
    - stages (ordered)
      - each stage's series (ordered by scheduled_date desc)
    - registered teams (TournamentTeam w/ seed and team info)

    This feeds the tournament detail page (public site),
    and is also great for admin/desktop review.
    """

    # Series for each Stage, with teams already joined
    series_prefetch = Prefetch(
        "series",
        queryset=Series.objects.select_related(
            "team1",
            "team2",
            "winner",
        ).order_by("-scheduled_date"),
    )

    # Stages for the Tournament, each with its Series
    stage_prefetch = Prefetch(
        "stages",
        queryset=Stage.objects.prefetch_related(series_prefetch).order_by(
            "order",
            "start_date",
        ),
    )

    # Registered / invited / qualified teams for this Tournament
    teams_prefetch = Prefetch(
        "tournamentteam_set",
        queryset=TournamentTeam.objects.select_related("team").order_by(
            "seed",
            "team__short_name",
        ),
    )

    return (
        Tournament.objects
        .filter(pk=tournament_id)
        .prefetch_related(stage_prefetch, teams_prefetch)
        .first()
    )


def get_series_detail(series_id: int):
    """
    Return one Series with:
    - tournament, stage, team1, team2, winner
    - all Games in that series
      - each Game's teams (blue_side/red_side/winner)
      - per-team stats (TeamGameStat)
      - per-player stats (PlayerGameStat)
      - draft actions (through its reverse FK gamedraftaction_set)

    This powers your match detail page.
    """

    games_prefetch = Prefetch(
        "games",
        queryset=Game.objects.select_related(
            "blue_side",
            "red_side",
            "winner",
        )
        .prefetch_related(
            # team-level totals (blue vs red)
            Prefetch(
                "team_stats",
                queryset=TeamGameStat.objects.select_related(
                    "team",
                ).order_by("side"),
            ),
            # player-level stats (ordered by side then IGN for nice table display)
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
            # draft picks / bans per game
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
    All Series for a given Stage, ordered by scheduled_date ascending.

    Useful for:
    - Stage tab / bracket view
    - Broadcast rundown (what's next today in playoffs group A, etc.)
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


def get_team_recent_series(team_id: int, limit: int = 10):
    """
    A team's last N series (either as team1 or team2), newest first.

    Used in:
    - Team profile 'Recent Results' widget
    - Talent research / desk prep
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


def get_active_tournaments():
    """
    Return tournaments that still matter right now:
    - UPCOMING (future scheduled, not started)
    - ONGOING (in progress)

    This powers /api/v1/tournaments/ list, default view.
    We also prefetch:
      - stages → their series
      - registered teams (TournamentTeam)
    so the frontend can show structure without extra queries.
    """

    stage_series_prefetch = Prefetch(
        "series",
        queryset=Series.objects.select_related(
            "team1",
            "team2",
            "winner",
        ).order_by("-scheduled_date"),
    )

    stages_prefetch = Prefetch(
        "stages",
        queryset=Stage.objects.prefetch_related(stage_series_prefetch).order_by(
            "order",
            "start_date",
        ),
    )

    teams_prefetch = Prefetch(
        "tournamentteam_set",
        queryset=TournamentTeam.objects.select_related("team").order_by(
            "seed",
            "team__short_name",
        ),
    )

    return (
        Tournament.objects
        .filter(status__in=["UPCOMING", "ONGOING"])
        .prefetch_related(stages_prefetch, teams_prefetch)
        .order_by("-start_date")
    )


def get_series_for_tournament(tournament_id: int):
    """
    All Series across all stages for a given tournament.
    Ordered chronologically.

    This can power:
    - Tournament "All Matches" tab
    - Ranking / rating engine (head-to-head input)
    - Export for analytics
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
        .filter(tournament_id=tournament_id)
        .order_by("scheduled_date")
    )