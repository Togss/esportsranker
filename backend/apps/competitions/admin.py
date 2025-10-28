from django.contrib import admin
from django import forms
from django.db.models import F, DurationField, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.db import transaction
from django.http import JsonResponse
from django.urls import path

from apps.competitions.models import (
    Tournament, Stage, Series, Game,
    TeamGameStat, PlayerGameStat, GameDraftAction, TournamentTeam
)
from apps.teams.models import Team
from apps.common.admin import RoleProtectedAdmin


# ---------- Inlines ----------
class SeriesInline(admin.TabularInline):
    model = Series
    extra = 0
    fields = (
        "match_summary",
        "team1",
        "team2",
        "best_of",
        "scheduled_date",
        "score",
        "winner"
    )
    ordering = ("-scheduled_date",)
    show_change_link = True
    readonly_fields = ("match_summary", "score")
    autocomplete_fields = ("team1", "team2", "winner")
    verbose_name_plural = "Series in this Stage"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("team1", "team2", "winner")
    
    @admin.display(description="Matchup")
    def match_summary(self, obj: Series):
        t1 = getattr(obj.team1, "short_name", str(obj.team1_id))
        t2 = getattr(obj.team2, "short_name", str(obj.team2_id))
        bo = f"Bo{obj.best_of}" if obj.best_of else "BoN"

        return f"{t1} vs {t2} ({bo})".strip()
    

class StageInline(admin.TabularInline):
    model = Stage
    extra = 0
    fields = (
        "stage_type",
        "variant",
        "order",
        "tier",
        "start_date",
        "end_date"
    )
    ordering = ("order",)
    show_change_link = True

class TeamGameStatInline(admin.TabularInline):
    model = TeamGameStat
    can_delete = False
    extra = 0
    max_num = 2
    fields = (
        "team",
        "side",
        "game_result",
        "gold",
        "t_score",
        "tower_destroyed",
        "lord_kills",
        "turtle_kills",
        "orange_buff",
        "purple_buff",
    )
    readonly_fields = ("team", "side")
    verbose_name_plural = "Team Game Stats (Blue/Red Side)"

    def get_formset(self, request, obj=None, **kwargs):
        self._parent_obj = obj
        return super().get_formset(request, obj, **kwargs)
    
    def clean(self):
        super().clean()
        if not getattr(self, "_parent_obj", None):
            return
        rows = [f.cleaned_data for f in self.forms if hasattr(f, "cleaned_data") and f.cleaned_data and not f.cleaned_data.get("DELETE", False)]
        if len(rows) != 2:
            raise ValidationError("You must enter stats for both teams (Blue and Red side).")
        

class _BaseSideFormSet(BaseInlineFormSet):
    SIDE = None

    def _side_team(self):
        game = self.instance
        return game.blue_side if self.SIDE == "BLUE" else game.red_side
    
    def _side_teamstat(self):
        game = self.instance
        team = self._side_team()

        tgs, _ = TeamGameStat.objects.get_or_create(
            game=game,
            team=team,
            defaults={"side": self.SIDE}
        )
        return tgs
    
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        obj.game = self.instance
        obj.team = self._side_team()
        obj.team_stat = self._side_teamstat()
        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        instance.game = self.instance
        instance.team = self._side_team()
        instance.team_stat = self._side_teamstat()
        return super().save_existing(form, instance, commit)
    
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            cd = getattr(form, "cleaned_data", None)
            if not cd or cd.get("DELETE"):
                continue

            if any(cd.get(f) for f in (
                "player",
                "hero",
                "k",
                "d",
                "a",
                "gold",
                "dmg_dealt",
                "dmg_taken",
                "is_MVP"
            )):
                count += 1
        if count > 5:
            raise ValidationError("You can only enter stats for up to 5 players per team.")
        
class BlueSideFormSet(_BaseSideFormSet):
    SIDE = "BLUE"

class RedSideFormSet(_BaseSideFormSet):
    SIDE = "RED"

class _BasePlayerStatInline(admin.TabularInline):
    model = PlayerGameStat
    can_delete = True
    extra = 5
    max_num = 5
    exclude = ("team_stat", "team")
    fields = (
        "player",
        "role",
        "hero",
        "k",
        "d",
        "a",
        "gold",
        "dmg_dealt",
        "dmg_taken",
        "is_MVP"
    )

class BlueSidePlayerStatInline(_BasePlayerStatInline):
    verbose_name_plural = "Blue Side Player Game Stats"
    formset = BlueSideFormSet

class RedSidePlayerStatInline(_BasePlayerStatInline):
    verbose_name_plural = "Red Side Player Game Stats"
    formset = RedSideFormSet


class GameDraftActionInline(admin.TabularInline):
    model = GameDraftAction
    extra = 10
    max_num = 20
    fields = (
        "action",
        "side",
        "order",
        "hero",
        "player"
    )
    ordering = ("order",)
    verbose_name_plural = "Draft Actions (Ban/Pick Order)"


class TournamentTeamInline(admin.TabularInline):
    model = TournamentTeam
    extra = 0
    autocomplete_fields = ("team",)
    fields = (
        "team",
        "seed",
        "kind",
        "group",
        "notes"
    )
    ordering = ("seed", "team__short_name")


# ---------- Admins ----------

@admin.register(Tournament)
class TournamentAdmin(RoleProtectedAdmin):
    list_display = (
        "logo_thumb",
        "name",
        "region",
        "team_count",
        "tier",
        "status",
        "start_date",
        "end_date"
    )
    list_filter = ("region", "tier", "status")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-start_date", "name")
    readonly_fields = (
        "logo_preview",
        "status",
        "created_at",
        "updated_at",
        "stage_label",
        "created_by",
        "updated_by"
    )
    inlines = [StageInline, TournamentTeamInline]

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "slug",
                "region",
                "tier",
                "status"
            )
        }),
        ("Schedule", {
            "fields": (
                "start_date",
                "end_date"
            )
        }),
        ("Public Info", {
            "fields": (
                "description",
                "rules_link",
                "prize_pool"
            )
        }),
        ("Branding", {
            "fields": (
                "logo",
                "logo_preview"
            )
        }),
        (
            "Audit Info", {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by"
                )
            }
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    # --- Custom Displays ---
    @admin.display(description="Logo")
    def logo_thumb(self, obj: Tournament):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:28px;width:28px;border-radius:4px;object-fit:cover;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="height:28px;width:28px;border-radius:4px;'
            'background-color:#ccc;display:flex;align-items:center;justify-content:center;'
            'color:#666;font-size:14px;">N/A</div>'
        )
    
    @admin.display(description="Logo Preview")
    def logo_preview(self, obj: Tournament):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height:120px;max-width:200px;border-radius:8px;object-fit:cover;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="height:120px;width:200px;border-radius:8px;'
            'background-color:#ccc;display:flex;align-items:center;justify-content:center;'
            'color:#666;font-size:18px;">No Logo Uploaded</div>'
        )
    
    @admin.display(description="Teams")
    def team_count(self, obj: Tournament):
        return obj.teams.count()
    
    @admin.display(description="Stages")
    def stage_label(self, obj: Tournament):
        rows = (
            obj.stages.all()
            .order_by("order")
            .values_list("stage_type", "variant")
        )
        if not rows:
            return "—"
      
        type_map = dict(getattr(Stage, "STAGE_TYPES", []))

        labels = []
        for stages_type, variant in rows:
            base = type_map.get(stages_type, stages_type)
            if variant:
                labels.append(f"{base} - {variant}")
            else:
                labels.append(base)
        return " • ".join(labels)
    
# ----- Stage Admin -----
@admin.register(Stage)
class StageAdmin(RoleProtectedAdmin):
    # What you see in the /admin/competitions/stage/ list view
    list_display = (
        "stage_label",      # e.g. "Playoffs Stage - Upper Bracket"
        "tournament",       # MPL PH S13
        "order",            # 1, 2, 3...
        "status",           # UPCOMING / ONGOING / COMPLETED
        "start_date",
        "end_date",
    )

    list_filter = (
        "tournament",
        "status",
    )

    search_fields = (
        "stage_type",
        "variant",
        "tournament__name",
    )

    # Slug auto-fills from stage_type + variant while you're typing
    prepopulated_fields = {
        "slug": ("stage_type", "variant"),
    }

    # Order: First by tournament’s start date, then within that by "order"
    ordering = (
        "tournament__start_date",
        "order",
    )

    # Tournament FK can get big, so this prevents a giant dropdown
    autocomplete_fields = (
        "tournament",
    )

    # These should not be edited directly in admin
    readonly_fields = (
        "status",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by"
    )

    # Inline: show all Series (matches) that belong to this Stage
    inlines = [SeriesInline]

    fieldsets = (
        (None, {
            "fields": (
                "tournament",
                "stage_type",
                "variant",
                "slug",
                "order",
                "tier",
            )
        }),
        ("Schedule", {
            "fields": (
                "start_date",
                "end_date",
            )
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": (
                "status",
                "created_at",
                "updated_at",
                "created_by",
                "updated_by"
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Optimize: We always show tournament in list_display,
        so select_related reduces queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related("tournament")

    @admin.display(description="Stage")
    def stage_label(self, obj: Stage):
        """
        Human-friendly stage label for list_display.
        Examples:
        - "Group Stage"
        - "Playoffs Stage - Upper Bracket"
        - "Grand Finals"
        """
        # If stage_type is using STAGE_TYPES choices, we can get its label using .get_FOO_display()
        if hasattr(obj, "get_stage_type_display"):
            base_label = obj.get_stage_type_display()
        else:
            # fallback if not a choices field
            base_label = obj.stage_type

        if obj.variant:
            return f"{base_label} - {obj.variant}"
        return base_label


# ----- Series: limit Stage/Teams to the selected Tournament -----

class SeriesAdminForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        tournament = self.instance.tournament if self.instance and self.instance.pk else self.initial.get("tournament")
        # If creating (no instance yet), try to read tournament from POST or GET
        if not tournament:
            data = self.data or None
            if data and data.get("tournament"):
                try:
                    tournament = Tournament.objects.get(pk=data.get("tournament"))
                except Tournament.DoesNotExist:
                    tournament = None

        # Scope the Stage dropdown to this tournament
        if tournament and "stage" in self.fields:
            self.fields["stage"].queryset = Stage.objects.filter(tournament=tournament).order_by("order")

        # Scope team1/team2 to tournament-registered teams if you maintain M2M; else leave all teams
        if tournament and hasattr(tournament, "teams"):
            t_teams = tournament.teams.all()
            if "team1" in self.fields:
                self.fields["team1"].queryset = t_teams
            if "team2" in self.fields:
                self.fields["team2"].queryset = t_teams


@admin.register(Series)
class SeriesAdmin(RoleProtectedAdmin):
    form = SeriesAdminForm
    list_display = ("series_matchup", "stage", "score", "winner", "best_of", "scheduled_date")
    list_filter = ("tournament", "stage", "best_of")
    search_fields = (
        "tournament__name", "tournament__short_name",
        "team1__name", "team1__short_name", "team2__name", "team2__short_name"
    )
    ordering = ("-scheduled_date",)
    autocomplete_fields = ("tournament", "stage", "team1", "team2", "winner")
    readonly_fields = ("score", "winner", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (None, {"fields": ("tournament", "stage", "team1", "team2", "best_of", "scheduled_date")}),
        ("Results", {"fields": ("score", "winner")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Series Matchup")
    def series_matchup(self, obj):
        return f"{obj.team1} vs {obj.team2}"
    
    @admin.display(description="Score")
    def score(self, obj):
        if obj.team1_score is not None and obj.team2_score is not None:
            return f"{obj.team1_score} - {obj.team2_score}"
        return "—"
    
    # Display team_short_name for winner
    @admin.display(description="Winner")
    def winner(self, obj):
        if obj.winner:
            return obj.winner.short_name
        return "—"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("tournament", "stage", "team1", "team2", "winner")


# ----- Game: one-screen data entry (stats + draft) & limit sides to series teams -----

class GameAdminForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = "__all__"
        widgets = {
            "duration": forms.HiddenInput(),
        }

    duration_display = forms.CharField(label="Duration (MM:SS)", required=False, help_text="Enter duration in minutes and seconds (e.g., 25:30 for 25 minutes and 30 seconds).")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill MM:SS from duration
        if self.instance and self.instance.duration:
            total_seconds = int(self.instance.duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            self.fields["duration_display"].initial = f"{minutes:02d}:{seconds:02d}"

        # Limit blue/red/winner to the series teams
        series = self.instance.series if (self.instance and self.instance.pk) else None
        if not series:
            sid = self.data.get("series") or self.initial.get("series")
            if sid:
                try:
                    series = Series.objects.select_related("team1", "team2").get(pk=sid)
                except Series.DoesNotExist:
                    series = None
        if series:
            teams_qs = Team.objects.filter(pk__in=[series.team1_id, series.team2_id])
            if "blue_side" in self.fields:
                self.fields["blue_side"].queryset = teams_qs
            if "red_side" in self.fields:
                self.fields["red_side"].queryset = teams_qs
            if "winner" in self.fields:
                self.fields["winner"].queryset = teams_qs
                self.fields["winner"].help_text = f"Select the winning team ({series.team1.short_name} or {series.team2.short_name})."

        # Improve input UX
        self.fields["duration_display"].widget.attrs.update({
            "placeholder": "MM:SS",
            "pattern": r"^\d{1,3}:\d{2}$",
            "inputmode:": "numeric",
        })

    def clean_duration_display(self):
        value = (self.cleaned_data.get("duration_display") or "").strip()
        if value == "":
            return None
        parts = value.split(":")
        if len(parts) != 2:
            raise ValidationError("Duration must be in MM:SS format.")
        try:
            minutes = int(parts[0])
            seconds = int(parts[1])
            if seconds < 0 or seconds >= 60 or minutes < 0:
                raise ValueError
        except ValueError:
            raise ValidationError("Invalid duration format. Please enter valid minutes and seconds.")
        if not (0 <= seconds <= 59):
            raise ValidationError("Seconds must be between 0 and 59.")
        return timedelta(minutes=minutes, seconds=seconds)
    
    def save(self, commit=True):
        has_display = "duration_display" in self.cleaned_data
        display_val = self.cleaned_data.get("duration_display")
        if has_display and display_val is not None:
            self.instance.duration = display_val
        return super().save(commit=commit)
    
@admin.register(Game)
class GameAdmin(RoleProtectedAdmin):
    form = GameAdminForm
    list_display = (
        "game_no",
        "series",
        "blue_side",
        "red_side",
        "duration",
        "winner"
    )
    list_filter = ("series__tournament", "series__stage", "result_type")
    search_fields = (
        "series__team1__name", "series__team1__short_name",
        "series__team2__name", "series__team2__short_name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by"
    )
    fieldsets = (
        (None, {
            "fields": (
                "series",
                "game_no",
                "blue_side",
                "red_side",
                "result_type",
                "winner",
                "duration_display",
                "vod_link",
            )
        }),        
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": (
                "created_by",
                "updated_by",
                "created_at",
                "updated_at"
            )
        }),
    )
    inlines = [
        GameDraftActionInline,
        TeamGameStatInline,
        BlueSidePlayerStatInline,
        RedSidePlayerStatInline,
    ]

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user

        is_creating = not change

        super().save_model(request, obj, form, change)

        if is_creating and obj.blue_side_id and obj.red_side_id:
            def _after_commit():
                blue_stat, created_blue = TeamGameStat.objects.get_or_create(
                    game=obj,
                    team_id=obj.blue_side_id,
                    defaults={
                        "side": "BLUE",
                        "created_by": request.user,
                        "updated_by": request.user
                    },
                )
                if not created_blue:
                    if blue_stat.updated_by_id != request.user.id:
                        blue_stat.updated_by = request.user
                        blue_stat.save(update_fields=["updated_by", "updated_at"])

                red_stat, created_red = TeamGameStat.objects.get_or_create(
                    game=obj,
                    team_id=obj.red_side_id,
                    defaults={
                        "side": "RED",
                        "created_by": request.user,
                        "updated_by": request.user
                    },
                )
                if not created_red:
                    if red_stat.updated_by_id != request.user.id:
                        red_stat.updated_by = request.user
                        red_stat.save(update_fields=["updated_by", "updated_at"])
            transaction.on_commit(_after_commit)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)

        game = form.instance

        if isinstance(formset, (BlueSideFormSet, RedSideFormSet, TeamGameStatInline.formset)):
            team_stats = TeamGameStat.objects.filter(game=game)

            for ts in team_stats:
                changed_fields = []

                if ts.created_by_id is None:
                    ts.created_by = request.user
                    changed_fields.append("created_by")

                if ts.updated_by_id != request.user.id:
                    ts.updated_by = request.user
                    changed_fields.append("updated_by")

                if changed_fields:
                    if "updated_by" in changed_fields and "updated_at" not in changed_fields:
                        changed_fields.append("updated_at")
                    ts.save(update_fields=changed_fields)
        
        if isinstance(formset, (BlueSideFormSet, RedSideFormSet)):
            self._defer_player_count_check = True
            self._last_game_for_count = game

    def response_add(self, request, obj, post_url_continue=None):
        self._final_check_10_players(request, obj)
        return super().response_add(request, obj, post_url_continue)
    
    def response_change(self, request, obj):
        self._final_check_10_players(request, obj)
        return super().response_change(request, obj)

    def _final_check_10_players(self, request, game):
        if not getattr(self, "_defer_player_count_check", False):
            return
        
        game = getattr(self, "_last_game_for_count", None)
        if not game:
            return
        
        blue_count = PlayerGameStat.objects.filter(
            game=game,
            team_stat__side="BLUE"
        ).count()
        red_count = PlayerGameStat.objects.filter(
            game=game,
            team_stat__side="RED"
        ).count()

        if blue_count != 5 or red_count !=5:
            from django.contrib import messages
            messages.error(
                request,
                f"Player Stats Incomplete: Blue Side has {blue_count}/5 players, Red Side has {red_count}/5 players. Please ensure each side has exactly 5 player stats entered."
            )

            self._defer_player_count_check = False
            self._last_game_for_count = None

# ---------- Read-Only Admins for Stats/Draft ----------
def _readonly_fields_for(model):
    # all model fields become read-only in the change view
    return [f.name for f in model._meta.fields] + [m.name for m in model._meta.many_to_many]

@admin.register(TeamGameStat)
class TeamGameStatReadonlyAdmin(RoleProtectedAdmin):
    list_display = ('team', 'game', 'side', 'game_result', 'gold', 't_score',
                    'tower_destroyed', 'lord_kills', 'turtle_kills',
                    'orange_buff', 'purple_buff')
    list_filter = ('side', 'game_result', 'game__series__tournament', 'game__series')
    search_fields = ('game__series__tournament__name', 'team__name')
    ordering = ('game', 'team')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def get_readonly_fields(self, request, obj=None):
        return _readonly_fields_for(TeamGameStat)

@admin.register(PlayerGameStat)
class PlayerGameStatReadonlyAdmin(RoleProtectedAdmin):
    list_display = ('player', 'team', 'game', 'role', 'hero', 'k', 'd', 'a',
                    'gold', 'dmg_dealt', 'dmg_taken', 'is_MVP')
    list_filter = ('role', 'team', 'game__series__tournament', 'game__series')
    search_fields = ('player__name', 'game__series__tournament__name', 'team__name')
    ordering = ('game', 'team', 'player')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def get_readonly_fields(self, request, obj=None):
        return _readonly_fields_for(PlayerGameStat)

@admin.register(GameDraftAction)
class GameDraftActionReadonlyAdmin(RoleProtectedAdmin):
    list_display = ('game', 'order', 'action', 'side', 'hero', 'player')
    list_filter = ('action', 'side', 'game__series__tournament', 'game__series')
    search_fields = ('hero__name', 'player__name', 'game__series__tournament__name')
    ordering = ('game', 'order')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def get_readonly_fields(self, request, obj=None):
        return _readonly_fields_for(GameDraftAction)
