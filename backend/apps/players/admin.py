from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db import models
from django.db.models import OuterRef, Q
from .models import Player, PlayerMembership


class PlayerMembershipInline(admin.TabularInline):
    model = PlayerMembership
    extra = 0
    autocomplete_fields = ['team']
    fields = ('team', 'role_at_team', 'start_date', 'end_date', 'is_starter')
    ordering = ('-start_date',)
    show_change_link = True


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'photo_thumb',
        'ign',
        'role',
        'current_team_for_list',
        'nationality',
        'is_active'
    )
    list_filter = (
        'role',
        'nationality',
        'is_active',
        'memberships__team'
    )
    search_fields = (
        'ign',
        'name',
        'memberships__team__short_name',
        'memberships__team__name'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'photo_preview',
        'created_by',
        'updated_by'
    )
    prepopulated_fields = {
        'slug': ('ign',)
    }
    ordering = (
        'memberships__team__short_name',
        'ign'
    )
    inlines = [PlayerMembershipInline]

    fieldsets = (
        ('Identity', {
            'fields': (
                'ign', 'role', 'name', 'slug', 'nationality', 'date_of_birth'
            )
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
        ('Audit Info', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change or not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        field_name = request.GET.get('field_name')

        if field_name == 'player':
            today = timezone.localdate()
            active_memberships = PlayerMembership.objects.filter(
                player=OuterRef('pk'),
                start_date__lte=today
            ).filter(
                Q(end_date__gte=today) | Q(end_date__isnull=True)
            )
            queryset = (
                queryset
                .filter(is_active=True)
                .annotate(has_active_membership=models.Exists(active_memberships))
                .filter(has_active_membership=False)
                .order_by('ign')
            )
        return queryset, use_distinct

    @admin.display(description='Current Team')
    def current_team_for_list(self, obj: Player):
        today = timezone.localdate()
        m = (
            obj.memberships.filter(start_date__lte=today)
            .filter(models.Q(end_date__gte=today) | models.Q(end_date__isnull=True))
            .select_related('team')
            .first()
        )
        return m.team.short_name if m else "Free Agent"

    @admin.display(description='Photo')
    def photo_thumb(self, obj: Player):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:28px;width:28px;border-radius:50%;object-fit:cover;" />',
                obj.photo.url,
            )
        return format_html(
            '<div style="width:28px;height:28px;border-radius:50%;background:#ddd;display:flex;align-items:center;justify-content:center;font-size:10px;color:#666;">–</div>'
        )

    @admin.display(description='Photo Preview')
    def photo_preview(self, obj: Player):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:140px;width:auto;border-radius:12px;object-fit:cover;" />',
                obj.photo.url,
            )
        return format_html(
            '<div style="width:140px;height:140px;border:1px dashed #ccc;display:flex;align-items:center;justify-content:center;color:#888;">No Photo</div>'
        )