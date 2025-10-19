from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from .models import Player, PlayerMembership

class PlayerMembershipInline(admin.TabularInline):
    model = PlayerMembership
    extra = 0
    autocomplete_fields = ['team']
    fields = 'team', 'role_at_team', 'start_date', 'end_date', 'is_starter'
    ordering = ('-start_date',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('photo_thumb', 'ign', 'role', 'current_team_for_list', 'nationality', 'is_active')
    list_filter = ('role', 'nationality', 'is_active', 'memberships__team')
    search_fields = ('ign', 'real_name', 'memberships__team__short_name', 'memberships__team__name')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview')
    prepopulated_fields = {'slug': ('ign',)}
    ordering = ('ign',)
    fieldsets = (
        ('Identity', {
            'fields': ('ign', 'role', 'real_name', 'slug', 'nationality', 'date_of_birth')
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview'),
            'description': 'Upload a clear portrait (PNG with transparent background preferred)'
        }),
        ('About', {
            'fields': ('achievements', 'is_active')
        }),
        ('Social Media', {
            'fields': ('x', 'facebook', 'instagram', 'youtube')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [PlayerMembershipInline]

    def current_team_for_list(self, obj: Player):
        today = timezone.localdate()
        m = obj.memberships.filter(
            start_date__lte=today
        ).filter(
            models.Q(end_date__gte=today) | models.Q(end_date__isnull=True)
        ).select_related('team').first()
        return m.team.short_name if m else "Free Agent"
    current_team_for_list.short_description = 'Current Team'

    @admin.display(description='Photo')
    def photo_thumb(self, obj: Player):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:28px;width:auto;border-radius:50%;object-fit:cover;" />',
                obj.photo.url
            )
        return "No Photo"
    
    @admin.display(description='Photo Preview')
    def photo_preview(self, obj: Player):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:140px;width:auto;border-radius:12px;object-fit:cover;" />',
                obj.photo.url
            )
        return "No Photo"
