from rest_framework import serializers
from .models import Team


class TeamSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="get_region_display", read_only=True)
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "slug",
            "short_name",
            "region",
            "description",
            "achievements",
            "founded_year",
            "website",
            "x",
            "facebook",
            "youtube",
            "logo",
            "created_at",
            "updated_at",
        ]

    def get_logo(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        elif obj.logo:
            return obj.logo.url
        return None