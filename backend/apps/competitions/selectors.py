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
    GameDraftAction,
)
from apps.common.enums import TournamentStatus

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


def get_active_tournaments(limit: int = 20):
    """
    Return recent/active tournaments with nested prefetching so the public
    tournament list/landing can render without N+1 queries.
    """

    # base queryset: most recent first (upcoming/ongoing/completed still appears)
    base_qs = (
        Tournament.objects.filter(
            status__in=[
                TournamentStatus.UPCOMING,
                TournamentStatus.ONGOING,
                TournamentStatus.COMPLETED,
            ]
        )
        .order_by("-start_date")
    )

    # Prefetch tournament teams (with the actual team objects)
    tournament_teams_prefetch = Prefetch(
        "tournament_teams",  # ✅ matches related_name on TournamentTeam.tournament
        queryset=TournamentTeam.objects.select_related("team").only(
            "id",
            "tournament_id",
            "team_id",
            "seed",
            "kind",
            "group",
            "notes",
            "team__id",
            "team__short_name",
            "team__region",
            "team__slug",
        ),
        to_attr="prefetched_tournament_teams",  # optional nice-to-have
    )

    # Prefetch games (and their stats) under each series
    games_prefetch = Prefetch(
        "games",  # ✅ matches related_name='games' on Game.series
        queryset=Game.objects.select_related(
            "blue_side",
            "red_side",
            "winner",
            "series",
        )
        .prefetch_related(
            Prefetch(
                "team_stats",  # ✅ Game.team_stats related_name='team_stats'
                queryset=TeamGameStat.objects.select_related(
                    "team",
                ).only(
                    "id",
                    "game_id",
                    "team_id",
                    "side",
                    "gold",
                    "t_score",
                    "tower_destroyed",
                    "lord_kills",
                    "turtle_kills",
                    "orange_buff",
                    "purple_buff",
                    "game_result",
                    "team__short_name",
                    "team__slug",
                ),
                to_attr="prefetched_team_stats",
            ),
            Prefetch(
                "player_stats",  # ✅ Game.player_stats related_name='player_stats'
                queryset=PlayerGameStat.objects.select_related(
                    "player",
                    "team",
                    "hero",
                ).only(
                    "id",
                    "game_id",
                    "player_id",
                    "team_id",
                    "role",
                    "is_MVP",
                    "k",
                    "d",
                    "a",
                    "gold",
                    "dmg_dealt",
                    "dmg_taken",
                    "player__id",
                    "player__ign",
                    "team__short_name",
                    "hero__id",
                    "hero__name",
                ),
                to_attr="prefetched_player_stats",
            ),
            Prefetch(
                "draft_actions",  # ✅ Game.draft_actions related_name='draft_actions'
                queryset=GameDraftAction.objects.select_related(
                    "hero",
                    "player",
                    "team",
                ).only(
                    "id",
                    "game_id",
                    "action",
                    "side",
                    "order",
                    "hero_id",
                    "player_id",
                    "team_id",
                    "hero__name",
                    "player__ign",
                    "team__short_name",
                ),
                to_attr="prefetched_draft_actions",
            ),
        )
        .only(
            "id",
            "series_id",
            "game_no",
            "blue_side_id",
            "red_side_id",
            "winner_id",
            "duration",
            "vod_link",
            "result_type",
            "blue_side__short_name",
            "red_side__short_name",
            "winner__short_name",
        )
        .order_by("game_no"),
        to_attr="prefetched_games",
    )

    # Prefetch series (including games_prefetch above)
    series_prefetch = Prefetch(
        "series",  # ✅ Stage.series related_name='series'
        queryset=Series.objects.select_related(
            "team1",
            "team2",
            "winner",
            "tournament",
            "stage",
        )
        .prefetch_related(games_prefetch)
        .only(
            "id",
            "tournament_id",
            "stage_id",
            "team1_id",
            "team2_id",
            "winner_id",
            "best_of",
            "scheduled_date",
            "score",
            "team1__short_name",
            "team2__short_name",
            "winner__short_name",
            "stage__stage_type",
            "stage__variant",
        )
        .order_by("-scheduled_date"),
        to_attr="prefetched_series",
    )

    # Prefetch stages (including the series_prefetch above)
    stages_prefetch = Prefetch(
        "stages",  # ✅ Tournament.stages related_name='stages'
        queryset=Stage.objects.select_related(
            "tournament",
        )
        .prefetch_related(series_prefetch)
        .only(
            "id",
            "tournament_id",
            "stage_type",
            "variant",
            "order",
            "start_date",
            "end_date",
            "tier",
            "status",
        )
        .order_by("order"),
        to_attr="prefetched_stages",
    )

    # finally: return enriched queryset
    return (
        base_qs.prefetch_related(
            tournament_teams_prefetch,
            stages_prefetch,
        )[:limit]
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