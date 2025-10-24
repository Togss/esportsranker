from typing import Optional, Tuple
from .models import Series, Team

def compute_series_score_and_winner(series: Series) -> Tuple[str, Optional[Team]]:
    """
    Pure function: reads series.games and returns (score_str, winner_team_or_None).
    - Uses Game.winner (already set by game/team-stat logic)
    - Ignores games with NO_CONTEST or with winner=None
    - Does NOT write to the DB
    """
    # Guard: missing teams -> no winner, 0-0 score
    if not series.team1_id or not series.team2_id:
        return "0-0", None

    t1 = 0
    t2 = 0
    needed = (series.best_of // 2) + 1  # Bo3->2, Bo5->3, etc.

    # winner is a FK; select_related for efficiency
    for g in series.games.select_related("winner").all():
        # If your Game model sets winner=None for NO_CONTEST, this naturally skips it
        if g.winner_id == series.team1_id:
            t1 += 1
        elif g.winner_id == series.team2_id:
            t2 += 1

        # Early exit if someone has already clinched the series
        if t1 >= needed or t2 >= needed:
            break

    score_str = f"{t1}-{t2}"
    winner: Optional[Team] = (
        series.team1 if t1 >= needed else
        (series.team2 if t2 >= needed else None)
    )
    return score_str, winner