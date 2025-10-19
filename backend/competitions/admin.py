from django.contrib import admin
from django.utils.html import format_html
from .models import Tournament, Stage, Series, Game, Team, TeamGameStat, PlayerGameStat, GameDraftAction

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('logo_thumb', 'name', 'region', 'teams_count', 'status', 'start_date', 'end_date',)
    list_filter = ('tier', 'region', 'status', 'start_date', 'end_date')
    search_fields = ('name', 'region', 'slug')
    readonly_fields = ('logo_thumb', 'created_at', 'updated_at', 'status')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('status', '-start_date', 'name')
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug', 'region', 'tier', 'status')}),
        ('Brand', {
            'fields': ('logo', 'logo_thumb')}),
        ('About', {
            'fields': ('prize_pool', 'description', 'start_date', 'end_date', 'tournament_rules_link', 'teams')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')}),
    )

    def logo_thumb(self, obj):
        if getattr(obj, 'logo') and getattr(obj.logo, 'url'):
            return format_html('<img src="{}" style="height:24px;width:auto;border-radius:3px;object-fit:contain"/>', obj.logo.url)
        return "(No Logo)"
    logo_thumb.short_description = 'Logo'

    def teams_count(self, obj):
        return obj.teams.count()
    teams_count.short_description = 'Teams'

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('stage_type', 'tournament', 'order', 'status', 'start_date', 'end_date')
    list_filter = ('tournament', 'stage_type', 'start_date', 'end_date')
    search_fields = ('tournament__name', 'stage_type')
    readonly_fields = ('created_at', 'updated_at', 'status')
    ordering = ('tournament', 'order',)
    autocomplete_fields = ('tournament',)

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('stage_type', 'team1', 'team2', 'best_of', 'score', 'winner')
    list_filter = ('stage_type__tournament', 'best_of', 'winner')
    search_fields = ('stage_type__tournament__name', 'team1__short_name', 'team2__short_name')
    readonly_fields = ('created_at', 'updated_at', 'winner', 'score')
    ordering = ('tournament', 'stage_type', 'stage_type__order',)
    autocomplete_fields = ('stage_type', 'team1', 'team2', 'winner')