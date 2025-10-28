from rest_framework import serializers
from apps.competitions.models import (
    Tournament,
    Stage,
    Series,
    Game,
    TeamGameStat,
    PlayerGameStat,
    GameDraftAction,
)

# ───────────────────────────────
# Lowest-level serializers first
# ───────────────────────────────

class GameDraftActionSerializer(serializers.ModelSerializer):
    hero_name = serializers.CharField(source="hero.name", read_only=True)
    team_name = serializers.CharField(source="team.short_name", read_only=True)
    player_name = serializers.CharField(source="player.ign", read_only=True)

    class Meta:
        model = GameDraftAction
        fields = [
            "id", "action", "side", "order",
            "hero_name", "team_name", "player_name",
        ]


class PlayerGameStatSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.ign", read_only=True)
    hero_name = serializers.CharField(source="hero.name", read_only=True)
    team_name = serializers.CharField(source="team.short_name", read_only=True)

    class Meta:
        model = PlayerGameStat
        fields = [
            "id", "player_name", "team_name", "hero_name",
            "role", "is_MVP", "k", "d", "a",
            "gold", "dmg_dealt", "dmg_taken",
        ]


class TeamGameStatSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.short_name", read_only=True)

    class Meta:
        model = TeamGameStat
        fields = [
            "id", "team_name", "side",
            "tower_destroyed", "lord_kills", "turtle_kills",
            "orange_buff", "purple_buff", "game_result",
            "gold", "t_score",
        ]


class GameSerializer(serializers.ModelSerializer):
    blue_side = serializers.CharField(source="blue_side.short_name", read_only=True)
    red_side = serializers.CharField(source="red_side.short_name", read_only=True)
    winner_name = serializers.CharField(source="winner.short_name", read_only=True)
    team_stats = TeamGameStatSerializer(many=True, read_only=True)
    player_stats = PlayerGameStatSerializer(many=True, read_only=True)
    draft_actions = GameDraftActionSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            "id", "game_no", "blue_side", "red_side", "winner_name",
            "duration", "result_type", "vod_link",
            "team_stats", "player_stats", "draft_actions",
        ]


class SeriesSerializer(serializers.ModelSerializer):
    team1_name = serializers.CharField(source="team1.short_name", read_only=True)
    team2_name = serializers.CharField(source="team2.short_name", read_only=True)
    winner_name = serializers.CharField(source="winner.short_name", read_only=True)
    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = Series
        fields = [
            "id", "team1_name", "team2_name", "winner_name",
            "best_of", "scheduled_date", "score", "games",
        ]


class StageSerializer(serializers.ModelSerializer):
    series = SeriesSerializer(many=True, read_only=True)

    class Meta:
        model = Stage
        fields = [
            "id", "stage_type", "variant", "order",
            "start_date", "end_date", "tier", "status",
            "series",
        ]


class TournamentSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    stages = StageSerializer(many=True, read_only=True)

    class Meta:
        model = Tournament
        fields = [
            "id", "name", "slug", "region", "tier", "status",
            "start_date", "end_date", "prize_pool",
            "description", "rules_link", "logo", "stages",
        ]

    def get_logo(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        elif obj.logo:
            return obj.logo.url
        return None