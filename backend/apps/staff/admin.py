from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db import models
from django.db.models import Q, Exists, OuterRef

from .models import Staff, StaffMembership


class StaffMembershipInline(admin.TabularInline):
    model = StaffMembership
    extra = 0
    autocomplete_fields = ['team']
    fields = ('team', 'role_at_team', 'start_date', 'end_date')
    ordering = ('-start_date',)
    show_change_link = True


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'photo_thumb',
        'handle',
        'primary_role',
        'current_team_for_list',
        'nationality',
        'is_active',
    )
    list_filter = (
        'primary_role',
        'nationality',
        'is_active',
        'memberships__team',
    )
    search_fields = (
        'handle',
        'name',
        'memberships__team__short_name',
        'memberships__team__name',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'photo_preview',
    )
    prepopulated_fields = {'slug': ('handle',)}
    ordering = ('handle',)
    inlines = [StaffMembershipInline]

    fieldsets = (
        ('Identity', {
            'fields': (
                'handle',
                'primary_role',
                'name',
                'slug',
                'nationality',
            )
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview'),
            'description': 'Upload a clear portrait (PNG or transparent background if available)',
        }),
        ('About', {
            'fields': (
                'bio',
                'achievements',
                'is_active',
            )
        }),
        ('Social Media', {
            'fields': (
                'x',
                'facebook',
                'instagram',
                'youtube',
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    
    def get_search_results(self, request, queryset, search_term):
        """
        Limit autocomplete when adding staff to a team inline:
        Only show staff who are 'free agents' (not currently assigned).

        Free agent staff:
        - is_active=True
        - has NO StaffMembership that covers today
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        field_name = request.GET.get('field_name')

        # Only apply restriction when another admin form is trying to pick a Staff
        # for a ForeignKey named 'staff' (which we'll use in Team's inline).
        if field_name == 'staff':
            today = timezone.localdate()

            active_memberships = StaffMembership.objects.filter(
                staff=OuterRef('pk'),
                start_date__lte=today,
            ).filter(
                Q(end_date__gte=today) | Q(end_date__isnull=True)
            )

            queryset = (
                queryset
                .filter(is_active=True)
                .annotate(has_active_membership=Exists(active_memberships))
                .filter(has_active_membership=False)
                .order_by('handle')
            )

        return queryset, use_distinct

    @admin.display(description='Current Team')
    def current_team_for_list(self, obj: Staff):
        """
        Shows the staff member's current team (if they're actively contracted),
        or 'Free Agent' otherwise.
        """
        today = timezone.localdate()
        membership = (
            obj.memberships
            .filter(start_date__lte=today)
            .filter(Q(end_date__gte=today) | Q(end_date__isnull=True))
            .select_related('team')
            .first()
        )
        return membership.team.short_name if membership else 'Free Agent'

    @admin.display(description='Photo')
    def photo_thumb(self, obj: Staff):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:28px;width:28px;border-radius:50%;object-fit:cover;" />',
                obj.photo.url,
            )
        return format_html(
            '<div style="width:28px;height:28px;border-radius:50%;background:#ddd;'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:10px;color:#666;">–</div>'
        )

    @admin.display(description='Photo Preview')
    def photo_preview(self, obj: Staff):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:140px;width:auto;border-radius:12px;object-fit:cover;" />',
                obj.photo.url,
            )
        return format_html(
            '<div style="width:140px;height:140px;border:1px dashed #ccc;'
            'display:flex;align-items:center;justify-content:center;color:#888;">'
            'No Photo</div>'
        )