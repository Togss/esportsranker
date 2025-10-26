from rest_framework import serializers
from .models import StaffMembership, Staff

class StaffMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMembership
        fields = [
            'team',
            'role_at_team',
            'start_date',
            'end_date',
        ]


class StaffSerializer(serializers.ModelSerializer):
    nationality = serializers.SerializerMethodField()
    memberships = StaffMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id',
            'handle',
            'slug',
            'photo',
            'primary_role',
            'nationality',
            'memberships',
        ]

    def get_nationality(self, obj):
        return obj.nationality if obj.nationality else None
    
    def get_photo(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        elif obj.photo:
            return obj.photo.url
        return None