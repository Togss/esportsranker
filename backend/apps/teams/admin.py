from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from .models import Team
from apps.players.models import PlayerMembership
from apps.staff.models import StaffMembership

class TeamMembershipInline(admin.TabularInline):
    model = PlayerMembership
    extra = 0
    autocomplete_fields = ['player']
    fields = 'player', 'role_at_team', 'start_date', 'end_date', 'is_starter'
    ordering = ('-start_date',)
    show_change_link = True
    verbose_name_plural = 'Player / Roster Members'

class StaffMembershipInline(admin.TabularInline):
    model = StaffMembership
    extra = 0
    autocomplete_fields = ['staff']
    fields = ['staff', 'role_at_team', 'start_date', 'end_date']
    ordering = ('-start_date',)
    show_change_link = True
    verbose_name_plural = 'Coaching & Support Staff'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
          'logo_thumb',
          'short_name',
          'name',
          'region',
          'current_players_count',
          'is_active'
    )
    list_filter = ('region', 'is_active')
    search_fields = ('short_name', 'name', 'region', 'slug')
    readonly_fields = ('logo_preview', 'created_at', 'updated_at', 'created_by', 'updated_by')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-founded_year', 'name')
    fieldsets = (
        (
            'Identity',
            {
                'fields': ('short_name', 'name', 'slug', 'region')
            }
        ),
        (
            'Branding',
            {
                'fields': ('logo', 'logo_preview'),
                'description': 'Upload a square, transparent PNG for best results.'
            }
        ),
        (
            'About',
            {
                'fields': ('description', 'achievements', 'founded_year', 'is_active')
            }
        ),
        (
            'Social Media',
            {
                'fields': ('website', 'x', 'facebook', 'youtube')
            }
        ),
        (
            'Audit Info',
            {
                'classes': ('collapse',),
                'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
            }
        )
    )
    inlines = [StaffMembershipInline, TeamMembershipInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

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
            return format_html(
                '<div style="height:28px;width:28px;border-radius:4px;background-color:#e0e0e0;display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;">N/A</div>'
            )

    @admin.display(description='Logo Preview')
    def logo_preview(self, obj: Team):
            if obj.logo:
                return format_html(
                    '<img src="{}" style="height:100px;width:100px;border-radius:8px;object-fit:cover;" />',
                    obj.logo.url
                )
            return format_html(
                '<div style="height:100px;width:100px;border-radius:8px;background-color:#e0e0e0;display:flex;align-items:center;justify-content:center;color:#888;font-size:14px;">No Logo</div>'
            )