from typing import Optional, Tuple
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    Tournament,
    Stage,
    Series,
    Game,
    TeamGameStat,
    PlayerGameStat,
    TournamentTeam,
)
from apps.teams.models import Team


# ---------------------------------------------------------------------------------
# EXISTING FUNCTION (yours)
# ---------------------------------------------------------------------------------

def compute_series_score_and_winner(series: Series) -> Tuple[str, Optional[Team]]:
    if not series.team1_id or not series.team2_id:
        return "0-0", None

    t1 = 0
    t2 = 0
    needed = (series.best_of // 2) + 1  # Bo3->2, Bo5->3, Bo7->4

    # NOTE: we assume series.games has correct winners already
    for g in series.games.select_related("winner").all():
        if g.winner_id == series.team1_id:
            t1 += 1
        elif g.winner_id == series.team2_id:
            t2 += 1

        # Stop once someone has clinched
        if t1 >= needed or t2 >= needed:
            break

    score_str = f"{t1}-{t2}"
    winner: Optional[Team] = (
        series.team1 if t1 >= needed else
        (series.team2 if t2 >= needed else None)
    )
    return score_str, winner


# ---------------------------------------------------------------------------------
# NEW HELPERS
# ---------------------------------------------------------------------------------

def _ensure_team_in_tournament(tournament: Tournament, team: Team):
    """
    Guarantee a team is registered in the given tournament via TournamentTeam.
    Mirrors business rule you already enforce in Series.clean().
    """
    if not TournamentTeam.objects.filter(tournament=tournament, team=team).exists():
        raise ValidationError(
            f"Team {team} is not registered in {tournament}."
        )


# ---------------------------------------------------------------------------------
# PUBLIC WRITE SERVICES
# ---------------------------------------------------------------------------------

@transaction.atomic
def create_series(
    *,
    tournament: Tournament,
    stage: Stage,
    team1: Team,
    team2: Team,
    best_of: int,
    scheduled_date,
) -> Series:
    """
    Create a new Series in a safe, validated way.

    Used by:
    - Django Admin actions (optional later)
    - ingest API (desktop app sync in Phase 2)
    """

    # 1. stage must belong to tournament
    if stage.tournament_id != tournament.id:
        raise ValidationError("Stage does not belong to Tournament.")

    # 2. team1/team2 must be different
    if team1.id == team2.id:
        raise ValidationError("team1 and team2 must be different.")

    # 3. team1/team2 must both be registered for this tournament
    _ensure_team_in_tournament(tournament, team1)
    _ensure_team_in_tournament(tournament, team2)

    # 4. build instance
    series = Series(
        tournament=tournament,
        stage=stage,
        team1=team1,
        team2=team2,
        best_of=best_of,
        scheduled_date=scheduled_date,
    )

    # 5. run model validation (runs Series.clean())
    series.full_clean()

    # 6. save it
    series.save()

    # 7. OPTIONAL: pre-warm some state or logs in future if needed

    return series


@transaction.atomic
def record_game_result(
    *,
    game: Game,
    blue_side: Team,
    red_side: Team,
    winner: Optional[Team],
    result_type: str,
    duration=None,
    vod_link: Optional[str] = None,
) -> Game:
    """
    Update a Game with official result / duration / vod.
    Ensures TeamGameStat rows exist.

    After saving the game, we DO NOT yet push score up to Series here,
    because Series winner/score is computed from all games.
    That recalculation can be done by update_series_from_games().
    """

    # 1. update fields
    game.blue_side = blue_side
    game.red_side = red_side
    game.winner = winner
    game.result_type = result_type
    if duration is not None:
        game.duration = duration
    if vod_link is not None:
        game.vod_link = vod_link

    # 2. validate using Game.clean() rules (sides, unique game_no, etc.)
    game.full_clean()
    game.save()

    # 3. guarantee TeamGameStat objects for both sides
    TeamGameStat.objects.get_or_create(
        game=game,
        team=blue_side,
        defaults={"side": "BLUE"},
    )
    TeamGameStat.objects.get_or_create(
        game=game,
        team=red_side,
        defaults={"side": "RED"},
    )

    return game


@transaction.atomic
def update_series_from_games(series: Series) -> Series:
    """
    Recalculate and persist `series.score` and `series.winner`
    based on the current state of all its games.

    This is basically the "write" sister of compute_series_score_and_winner().
    Call this after you edit / add / finalize games.
    """

    score_str, winner_team = compute_series_score_and_winner(series)

    # Mutate and validate
    series.score = score_str
    series.winner = winner_team

    series.full_clean()
    series.save()

    return series