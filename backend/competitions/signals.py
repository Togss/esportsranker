from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Game, Series, TeamGameStat
from .services import compute_series_score_and_winner


@receiver([post_save, post_delete], sender=Game)
def update_series_after_game_change(sender, instance: Game, **kwargs):
    """
    Whenever a Game is saved or deleted, recompute its Series score and winner.
    """
    if not instance.series_id:
        return

    # Lock the row to prevent race conditions if multiple games update quickly
    with transaction.atomic():
        series = Series.objects.select_for_update().get(pk=instance.series_id)
        score_str, winner = compute_series_score_and_winner(series)

        # Update only if changed
        if series.score != score_str or series.winner_id != (winner.id if winner else None):
            series.score = score_str
            series.winner = winner
            series.save(update_fields=["score", "winner"])


WIN = "VICTORY"
LOSS = "DEFEAT"

def _compute_winner_from_team_stats(game: Game):
    """
    Decide the winner from TeamGameStat rows for a NORMAL game.
    Return a Team instance or None if undetermined/inconsistent.
    """
    stats = list(game.team_stats.select_related("team"))
    if not stats:
        return None

    victories = [ts for ts in stats if ts.game_result == WIN]
    if len(victories) == 1:
        return victories[0].team

    defeats = [ts for ts in stats if ts.game_result == LOSS]
    if len(defeats) == 1:
        # if exactly one defeat, the other team won
        loser = defeats[0].team
        if loser.id == game.blue_side_id:
            return game.red_side
        if loser.id == game.red_side_id:
            return game.blue_side

    return None


def _update_game_winner(game_id: int):
    """
    Lock the Game row and update its winner based on TeamGameStat (NORMAL only).
    """
    with transaction.atomic():
        game = Game.objects.select_for_update().select_related("series", "blue_side", "red_side").get(pk=game_id)

        # only derive from stats for NORMAL games
        if game.result_type != "NORMAL":
            return

        computed = _compute_winner_from_team_stats(game)
        if computed != game.winner:
            game.winner = computed
            game.save(update_fields=["winner"])


@receiver(post_save, sender=TeamGameStat)
def tgs_post_save(sender, instance: TeamGameStat, **kwargs):
    _update_game_winner(instance.game_id)


@receiver(post_delete, sender=TeamGameStat)
def tgs_post_delete(sender, instance: TeamGameStat, **kwargs):
    _update_game_winner(instance.game_id)


@receiver([post_save, post_delete], sender=Game)
def update_series_after_game_change(sender, instance: Game, **kwargs):
    if not instance.series_id:
        return
    with transaction.atomic():
        series = Series.objects.select_for_update().get(pk=instance.series_id)
        score_str, winner = compute_series_score_and_winner(series)
        if series.score != score_str or series.winner_id != (winner.id if winner else None):
            series.score = score_str
            series.winner = winner
            series.save(update_fields=["score", "winner"])