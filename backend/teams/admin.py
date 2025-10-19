from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django.db.models import OuterRef, Exists, Q
from .models import Team
from players.models import PlayerMembership, Player

class TeamMembershipInline(admin.TabularInline):
    model = PlayerMembership
    extra = 0
    autocomplete_fields = ['player']
    fields = 'player', 'role_at_team', 'start_date', 'end_date', 'is_starter'
    ordering = ('-start_date',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('logo_thumb', 'short_name', 'name', 'region', 'current_players_count', 'is_active')
    list_filter = ('region', 'is_active', 'founded_year')
    search_fields = ('short_name', 'name', 'region', 'slug')
    readonly_fields = ('logo_preview', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-founded_year', 'name')
    fieldsets = (
        ('Identity', {
            'fields': ('short_name', 'name', 'slug', 'region')}),
        ('Branding', {
            'fields': ('logo', 'logo_preview'),
            'description': 'Upload a square, transparent PNG for best results.'}),
        ('About', {
            'fields': ('description', 'achievements', 'founded_year', 'is_active')}),
        ('Social Media', {
            'fields': ('website', 'x', 'facebook', 'youtube')}),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')}),
    )
    inlines = [TeamMembershipInline]

    @admin.display(description='Current Players')
    def current_players_count(self, obj: Team):
            today = timezone.localdate()
            count = obj.memberships.filter(
                start_date__lte=today
            ).filter(
                models.Q(end_date__gte=today) | models.Q(end_date__isnull=True)
            ).count()
            return count

    @admin.display(description='Logo')
    def logo_thumb(self, obj: Team):
            if obj.logo:
                return format_html(
                    '<img src="{}" style="height:28px;width:28px;border-radius:4px;object-fit:cover;" />',
                    obj.logo.url
                )
            return "No Logo"

    @admin.display(description='Logo Preview')
    def logo_preview(self, obj: Team):
            if obj.logo:
                return format_html(
                    '<img src="{}" style="height:100px;width:100px;border-radius:8px;object-fit:cover;" />',
                    obj.logo.url
                )
            return "No Logo"