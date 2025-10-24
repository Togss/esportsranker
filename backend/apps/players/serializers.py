from rest_framework import serializers
from .models import Player

class PlayerSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    current_team = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            "id", "ign", "name", "slug", "role", "nationality", "date_of_birth",
            "photo_url", "achievements",
            "x", "facebook", "youtube", "instagram", "is_active",
            "current_team",  # computed, see get_current_team
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and hasattr(obj.photo, "url"):
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None

    def get_current_team(self, obj):
        """
        Uses annotations from the ViewSet if present, otherwise falls back to None.
        """
        tid = getattr(obj, "_current_team_id", None)
        if not tid:
            return None
        return {
            "id": tid,
            "name": getattr(obj, "_current_team_name", None),
            "short_name": getattr(obj, "_current_team_short_name", None),
            "slug": getattr(obj, "_current_team_slug", None),
        }