from rest_framework import serializers


class SeriesCreateSerializer(serializers.Serializer):
    """
    Payload to create a new Series (matchup) in a tournament stage.
    This matches competitions.services.create_series.
    """
    tournament_id = serializers.IntegerField()
    stage_id = serializers.IntegerField()
    team1_id = serializers.IntegerField()
    team2_id = serializers.IntegerField()
    best_of = serializers.IntegerField()
    scheduled_date = serializers.DateTimeField()


class GameResultUpdateSerializer(serializers.Serializer):
    """
    Payload to record/update a single game's result.
    This matches competitions.services.record_game_result.
    """
    game_id = serializers.IntegerField()
    blue_side_id = serializers.IntegerField()
    red_side_id = serializers.IntegerField()
    winner_id = serializers.IntegerField(allow_null=True)
    result_type = serializers.ChoiceField(choices=["NORMAL", "FF", "NO_CONTEST"])
    duration = serializers.DurationField(required=False, allow_null=True)
    vod_link = serializers.URLField(required=False, allow_null=True)