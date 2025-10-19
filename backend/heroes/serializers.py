from rest_framework import serializers
from .models import Hero

class HeroSerializer(serializers.ModelSerializer):
    hero_icon_url = serializers.SerializerMethodField()
    classes = serializers.SerializerMethodField()

    class Meta:
        model = Hero
        fields = [
            "id",
            "name",
            "slug",
            "primary_class",
            "secondary_class",
            "classes",
            "hero_icon_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_hero_icon_url(self, obj):
        request = self.context.get("request")
        if obj.hero_icon:
            return request.build_absolute_uri(obj.hero_icon.url) if request else obj.hero_icon.url
        return None

    def get_classes(self, obj):
        # returns readable combo, e.g. ["Fighter", "Assassin"]
        return obj.classes