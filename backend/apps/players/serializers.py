from rest_framework import serializers
from .models import Player, PlayerMembership


class PlayerMembershipSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.short_name", read_only=True)

    class Meta:
        model = PlayerMembership
        fields = [
            "team_name",
            "role_at_team",
            "start_date",
            "end_date",
            "is_starter",
            "is_active_today",
        ]


class PlayerSerializer(serializers.ModelSerializer):
    nationality = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)
    photo = serializers.SerializerMethodField()
    memberships = PlayerMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "name",
            "slug",
            "ign",
            "photo",
            "role",
            "age",
            "date_of_birth",
            "nationality",
            "achievements",
            "x",
            "facebook",
            "instagram",
            "youtube",
            "is_active",
            "memberships",
            "created_at",
            "updated_at",
        ]

    def get_photo(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        elif obj.photo:
            return obj.photo.url
        return None

    def get_nationality(self, obj):
        if obj.nationality:
            return obj.nationality.upper()
        return None