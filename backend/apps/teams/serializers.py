from rest_framework import serializers
from .models import Team

class TeamSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Team
        # name, slug, created_at, updated_at come from your common base
        fields = [
            "id", "name", "short_name", "slug", "region",
            "logo_url", "founded_year", "description", "achievements",
            "website", "x", "facebook", "youtube",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields  # read-only API for now

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if obj.logo and hasattr(obj.logo, "url"):
            return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
        return None