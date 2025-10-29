from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.db import models, transaction
from django.db.models import Q, F
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.apps import apps

from apps.common.models import TimeStampedModel, SluggedModel, UserStampedModel
from apps.common.enums import (
    Region,                # from teams/players week2 work
    TournamentTier,
    TournamentStatus,
    TournamentTeamKind,
    StageType,
    StageTier,
    StageStatus,
    SeriesLength,
    GameResultType,
    Side,
)
from apps.common.validators import (
    validate_start_before_end,
    validate_child_dates_within_parent,
    validate_same_tournament,
)
from apps.teams.models import Team
from apps.heroes.models import Hero
from apps.common.slug_helper import ensure_unique_slug, build_stage_slug_base


def tournament_logo_upload_to(instance, filename: str) -> str:
    parts = filename.rsplit(".", 1)
    ext = parts[1].lower() if len(parts) == 2 else "png"
    return f"tournament/logos/{instance.slug}.{ext}"


class Tournament(SluggedModel, TimeStampedModel, UserStampedModel):
    """
    Core tournament entity (M-Series, MPL PH S13, MSC 2024, etc.)
    """

    region = models.CharField(
        max_length=8,
        choices=Region.choices,
        db_index=True,
        help_text="Primary region or league this tournament belongs to (e.g. PH, ID, INTL).",
    )

    tier = models.CharField(
        max_length=5,
        choices=TournamentTier.choices,
        db_index=True,
        help_text="S-tier (world), A-tier (continental), B-tier (franchise league), etc.",
    )

    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)

    status = models.CharField(
        max_length=16,
        choices=TournamentStatus.choices,
        db_index=True,
    )

    teams = models.ManyToManyField(
        "teams.Team",
        through="competitions.TournamentTeam",
        related_name="tournaments",
        blank=True,
        help_text="Teams participating in this tournament.",
    )

    prize_pool = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Prize pool in USD.",
    )

    logo = models.ImageField(
        upload_to=tournament_logo_upload_to,
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        help_text="Public-facing description / summary for the tournament page.",
    )

    rules_link = models.URLField(
        blank=True,
        help_text="External link to official tournament rules / competitive rulebook.",
    )

    class Meta:
        ordering = ["-start_date", "name"]
        verbose_name = "Tournament"
        verbose_name_plural = "Tournaments"
        indexes = [
            models.Index(fields=["region"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["status"]),
            models.Index(fields=["region", "status"]),
            models.Index(fields=["tier", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(slug=""),
                name="tournament_slug_not_empty",
            ),
            models.UniqueConstraint(
                fields=["name", "start_date"],
                name="unique_tournament_name_start_date",
                deferrable=models.Deferrable.DEFERRED,
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F("start_date")),
                name="tournament_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        # Basic sanity: start <= end handled by constraint but we also give admin-friendly error.
        validate_start_before_end(
            self.start_date,
            self.end_date,
            field_start="start_date",
            field_end="end_date",
        )

    def compute_status(self) -> str:
        today = timezone.localdate()
        if self.start_date and self.end_date:
            if today < self.start_date:
                return TournamentStatus.UPCOMING
            elif self.start_date <= today <= self.end_date:
                return TournamentStatus.ONGOING
            else:
                return TournamentStatus.COMPLETED
        return TournamentStatus.UPCOMING

    def save(self, *args, **kwargs):
        # sync status every save
        self.status = self.compute_status()
        self.full_clean()
        super().save(*args, **kwargs)


class TournamentTeam(models.Model):
    """
    Through model for Tournament <-> Team.
    Stores seed, qualification type, group, notes.
    """

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="tournament_teams"
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="tournament_entries"
    )

    seed = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Seed / placement coming into the event (1 = top seed).",
    )

    kind = models.CharField(
        max_length=12,
        choices=TournamentTeamKind.choices,
        blank=True,
        help_text="How this team qualified (Invited / Qualified / Franchise).",
    )

    group = models.CharField(
        max_length=16,
        blank=True,
        help_text="Group/Pool name, e.g. 'Group A'.",
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional notes (sub roster, relegated, etc.).",
    )

    class Meta:
        ordering = ["seed", "team__short_name"]
        verbose_name = "Tournament Team"
        verbose_name_plural = "Tournament Teams"
        indexes = [
            models.Index(fields=["tournament", "team"]),
            models.Index(fields=["group"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "team"],
                name="unique_tournament_team",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        team_name = getattr(self.team, "short_name", str(self.team))
        return f"{team_name} ({self.tournament.name})"


class Stage(TimeStampedModel, UserStampedModel):
    """
    Subdivision of a Tournament.
    e.g. "Group Stage", "Playoffs - Upper Bracket", "Grand Finals"
    """

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='stages',
        db_index=True,
    )

    stage_type = models.CharField(
        max_length=20,
        choices=StageType.choices,
        db_index=True,
    )

    slug = models.SlugField(
        max_length=50,
        blank=True,
        unique=True,
        help_text="Auto-generated identifier for URLs / linking.",
    )

    variant = models.CharField(
        max_length=50,
        blank=True,
        help_text="Variant of the stage, e.g. 'Upper Bracket', 'Double Elimination'.",
    )

    order = models.PositiveIntegerField(
        help_text="Order of the stage in the tournament (1 = earliest).",
    )

    start_date = models.DateField(
        db_index=True,
        help_text="When this stage starts.",
    )

    end_date = models.DateField(
        db_index=True,
        help_text="When this stage ends.",
    )

    tier = models.CharField(
        max_length=2,
        choices=StageTier.choices,
        db_index=True,
        help_text="Tier weight for ranking calc (1 = highest).",
    )

    status = models.CharField(
        max_length=10,
        choices=StageStatus.choices,
        db_index=True,
        help_text="Auto-computed (Upcoming / Ongoing / Completed).",
    )

    class Meta:
        ordering = ['tournament', 'order']
        verbose_name = 'Stage'
        verbose_name_plural = 'Stages'
        indexes = [
            models.Index(fields=['tournament', 'stage_type', 'variant']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'stage_type', 'variant'],
                name='unique_stage_type_variant_per_tournament',
                deferrable=models.Deferrable.DEFERRED,
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F('start_date')),
                name='stage_end_date_after_start_date',
            ),
            models.UniqueConstraint(
                fields=['tournament', 'order'],
                name='unique_stage_order_per_tournament',
                deferrable=models.Deferrable.DEFERRED,
            ),
            models.CheckConstraint(
                check=Q(order__gte=1),
                name='stage_order_gte_1',
            ),
        ]

    def __str__(self):
        stage_type_label = dict(StageType.choices).get(
            self.stage_type,
            self.stage_type.title()
        )
        if self.variant:
            label = f"{stage_type_label} - {self.variant}"
        else:
            label = stage_type_label
        return f"{label} ({self.tournament.name})"

    def clean(self):
        super().clean()

        # chronological sanity (admin-friendly)
        validate_start_before_end(
            self.start_date,
            self.end_date,
            field_start="start_date",
            field_end="end_date",
        )

        # must belong to a tournament
        if not self.tournament_id:
            raise ValidationError({"tournament": "Tournament must be set for the stage."})

        # must fit within tournament window
        validate_child_dates_within_parent(
            child_start=self.start_date,
            child_end=self.end_date,
            parent_start=self.tournament.start_date,
            parent_end=self.tournament.end_date,
            parent_label="tournament dates",
            field_start="start_date",
            field_end="end_date",
        )

    def compute_status(self):
        today = timezone.localdate()
        if self.start_date and self.end_date:
            if today < self.start_date:
                return StageStatus.UPCOMING
            elif self.start_date <= today <= self.end_date:
                return StageStatus.ONGOING
            else:
                return StageStatus.COMPLETED
        return StageStatus.UPCOMING

    def save(self, *args, **kwargs):
        # slug build/ensure uniqueness
        base_candidate = self.slug or build_stage_slug_base(self)
        self.slug = ensure_unique_slug(
            base_candidate,
            self.__class__,
            instance_pk=self.pk,
        )

        # compute status before save
        self.status = self.compute_status()

        # enforce validations every save
        self.full_clean()
        super().save(*args, **kwargs)


class Series(TimeStampedModel, UserStampedModel):
    """
    Head-to-head matchup between two teams in a Stage.
    """

    tournament = models.ForeignKey(
        Tournament,
        related_name="series",
        on_delete=models.CASCADE,
        db_index=True,
    )

    stage = models.ForeignKey(
        Stage,
        related_name="series",
        on_delete=models.CASCADE,
        db_index=True,
    )

    team1 = models.ForeignKey(
        Team,
        related_name="series_as_team1",
        on_delete=models.CASCADE,
        db_index=True,
    )

    team2 = models.ForeignKey(
        Team,
        related_name="series_as_team2",
        on_delete=models.CASCADE,
        db_index=True,
    )

    winner = models.ForeignKey(
        Team,
        related_name="series_won",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        help_text="Auto-filled based on score calculation.",
    )

    best_of = models.PositiveIntegerField(
        choices=SeriesLength.choices,
        default=SeriesLength.BO3,
        null=True,
        blank=True,
        help_text="Length of the series (Bo3, Bo5...).",
    )

    scheduled_date = models.DateTimeField(
        db_index=True,
        help_text="Planned start (local time). Used for overdue data reminders.",
    )

    score = models.CharField(
        max_length=20,
        blank=True,
        help_text="Score in format 'Team1Score-Team2Score', e.g. '2-1'.",
    )

    class Meta:
        ordering = ["-scheduled_date"]
        verbose_name = "Series"
        verbose_name_plural = "Series"
        indexes = [
            models.Index(fields=["tournament"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["team1"]),
            models.Index(fields=["team2"]),
            models.Index(fields=["winner"]),
            models.Index(fields=["scheduled_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "stage", "team1", "team2", "scheduled_date"],
                name="unique_matchup_per_stage",
                deferrable=models.Deferrable.DEFERRED,
            ),
            models.CheckConstraint(
                check=~Q(team1=F("team2")),
                name="teams_must_be_different_in_series",
            ),
        ]

    def __str__(self):
        return f"{self.team1.short_name} vs {self.team2.short_name} – ({self.stage})"

    def compute_score_and_winner(self, persist: bool = True):
        from .services import compute_series_score_and_winner
        if not self.pk:
            return self.score, self.winner

        score_str, winner_team = compute_series_score_and_winner(self)
        winner_id = winner_team.id if winner_team else None
        if persist and self.pk:
            changed = (self.score != score_str) or (self.winner_id != winner_id)
            if changed:
                type(self).objects.filter(pk=self.pk).update(
                    score=score_str,
                    winner_id=winner_id,
                )
            self.score = score_str
            self.winner_id = winner_id
        return score_str, winner_team

    def clean(self):
        errors = {}

        if not self.tournament_id:
            errors["tournament"] = "Tournament must be set for the series."

        if not self.stage_id:
            errors["stage"] = "Stage must be set for the series."

        # Stage must point to same Tournament
        if self.stage_id and self.tournament_id:
            try:
                validate_same_tournament(
                    self.stage.tournament_id,
                    self.tournament_id,
                )
            except ValidationError as e:
                errors.update(e.message_dict)

        # team1 != team2 (DB constraint too, but surface nicely)
        if self.team1_id and self.team2_id and self.team1_id == self.team2_id:
            errors["team2"] = "Team 2 must be different from Team 1."

        # make sure both teams are registered in TournamentTeam
        TournamentTeam = apps.get_model('competitions', 'TournamentTeam')

        if self.tournament_id and self.team1_id:
            if not TournamentTeam.objects.filter(
                tournament_id=self.tournament_id,
                team_id=self.team1_id,
            ).exists():
                errors["team1"] = "Team 1 is not registered in this tournament."

        if self.tournament_id and self.team2_id:
            if not TournamentTeam.objects.filter(
                tournament_id=self.tournament_id,
                team_id=self.team2_id,
            ).exists():
                errors["team2"] = "Team 2 is not registered in this tournament."

        if errors:
            raise ValidationError(errors)

        super().clean()

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if not creating:
            self.compute_score_and_winner(persist=True)


class Game(TimeStampedModel, UserStampedModel):
    series = models.ForeignKey(Series, related_name='games', on_delete=models.CASCADE)

    game_no = models.PositiveIntegerField(
        help_text="Game number in the series, e.g., 1 for Game 1"
    )

    blue_side = models.ForeignKey(
        Team,
        related_name='games_as_blue_side',
        on_delete=models.CASCADE,
    )

    red_side = models.ForeignKey(
        Team,
        related_name='games_as_red_side',
        on_delete=models.CASCADE,
    )

    winner = models.ForeignKey(
        Team,
        related_name='games_won',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Duration of the game",
    )

    vod_link = models.URLField(
        blank=True,
        help_text="Link to the VOD of the game",
    )

    result_type = models.CharField(
        max_length=20,
        choices=GameResultType.choices,
        default=GameResultType.NORMAL,
    )

    class Meta:
        unique_together = ('series', 'game_no')
        ordering = ['series', 'game_no']
        verbose_name = 'Game'
        verbose_name_plural = 'Games'
        indexes = [
            models.Index(fields=['series', 'game_no']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['series', 'game_no'],
                name='unique_game_number_per_series',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=~Q(blue_side=F('red_side')),
                name='sides_must_be_different'
            ),
        ]

    def __str__(self) -> str:
        return f"G{self.game_no} - {self.series}"

    def get_side(self, team) -> str:
        team_id = getattr(team, 'id', team)
        if team_id == self.blue_side_id:
            return Side.BLUE
        elif team_id == self.red_side_id:
            return Side.RED
        return 'None'

    def clean(self):
        super().clean()
        errors = {}

        if not self.series_id:
            # if you try to fill sides/winner before choosing a Series in admin
            if self.blue_side_id and self.red_side_id or self.winner_id:
                errors['series'] = "Series must be set before setting sides or winner."
            if errors:
                raise ValidationError(errors)
            return

        # Blue/Red teams must match the series teams
        series_team_ids = {self.series.team1_id, self.series.team2_id}
        if self.blue_side_id and self.blue_side_id not in series_team_ids:
            errors['blue_side'] = "Blue side team must be one of the teams in the series."
        if self.red_side_id and self.red_side_id not in series_team_ids:
            errors['red_side'] = "Red side team must be one of the teams in the series."

        # Winner must be either blue or red
        if self.winner_id is not None and self.winner_id not in {self.blue_side_id, self.red_side_id}:
            errors['winner'] = "Winner must be either the blue side or red side team."

        # Blue and Red must differ (DB constraint enforces too, but message is nicer)
        if self.blue_side_id and self.red_side_id and self.blue_side_id == self.red_side_id:
            errors['red_side'] = "Red Side team must be different from Blue Side team."

        # game_no must be within best_of
        if self.game_no is not None and getattr(self.series, 'best_of', None):
            if not (1 <= self.game_no <= self.series.best_of):
                errors['game_no'] = f"Game number must be between 1 and {self.series.best_of} for this series."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        # Derive winner from result_type for forfeits / no contest
        if self.result_type == GameResultType.FORFEIT_TEAM1:
            self.winner = self.series.team1
        elif self.result_type == GameResultType.FORFEIT_TEAM2:
            self.winner = self.series.team2
        elif self.result_type == GameResultType.DRAW:
            self.winner = None

        self.full_clean()
        super().save(*args, **kwargs)

        # auto-create TeamGameStat rows for both sides after first save
        if creating and self.blue_side_id and self.red_side_id:
            def _ensure_team_stats():
                TeamGameStat.objects.get_or_create(
                    game=self,
                    team_id=self.blue_side_id,
                    defaults={'side': Side.BLUE}
                )
                TeamGameStat.objects.get_or_create(
                    game=self,
                    team_id=self.red_side_id,
                    defaults={'side': Side.RED}
                )
            transaction.on_commit(_ensure_team_stats)


class TeamGameStat(TimeStampedModel, UserStampedModel):
    VICTORY = 'VICTORY'
    DEFEAT = 'DEFEAT'

    RESULT_CHOICES = [
        (VICTORY, 'Win'),
        (DEFEAT, 'Loss'),
    ]

    game = models.ForeignKey(Game, related_name='team_stats', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='game_stats', on_delete=models.CASCADE)

    side = models.CharField(
        max_length=5,
        choices=Side.choices,
        db_index=True,
    )

    tower_destroyed = models.PositiveSmallIntegerField(default=0)
    lord_kills = models.PositiveSmallIntegerField(default=0)
    turtle_kills = models.PositiveSmallIntegerField(default=0)
    orange_buff = models.PositiveSmallIntegerField(default=0, help_text="Number of Orange Buffs secured")
    purple_buff = models.PositiveSmallIntegerField(default=0, help_text="Number of Purple Buffs secured")

    game_result = models.CharField(
        max_length=7,
        choices=RESULT_CHOICES,
        blank=True,
        help_text="Result of the game for the team"
    )

    gold = models.PositiveIntegerField(
        default=0,
        help_text="Total Gold Earned by the team"
    )

    t_score = models.PositiveSmallIntegerField(
        default=0,
        help_text="Total Team Score"
    )

    class Meta:
        ordering = ['game', 'team']
        verbose_name = 'Team Game Stat'
        verbose_name_plural = 'Team Game Stats'
        indexes = [
            models.Index(fields=['side']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'team'],
                name='unique_team_stat_per_game',
                deferrable=models.Deferrable.DEFERRED
            ),
        ]

    def __str__(self):
        return f"{self.team.short_name} Stats - {self.game}"

    def clean(self):
        super().clean()
        errors = {}

        # Ensure the team is actually in the game
        if self.team_id not in [self.game.blue_side_id, self.game.red_side_id]:
            errors['team'] = "Team must be one of the teams in the game."

        # side must match actual side of that team in this game
        expected_side = None
        if self.team_id == self.game.blue_side_id:
            expected_side = Side.BLUE
        elif self.team_id == self.game.red_side_id:
            expected_side = Side.RED

        if expected_side and self.side and self.side != expected_side:
            errors['side'] = f"Side must be '{expected_side}' for the selected team."

        # only one team should claim a given game_result per game
        if self.game.team_stats.exclude(pk=self.pk).filter(game_result=self.game_result).exists():
            errors['game_result'] = "Another team already has this game result for the same game."

        if errors:
            raise ValidationError(errors)

        # convenience autofill
        if expected_side and not self.side:
            self.side = expected_side
        if self.game.winner_id is not None and not self.game_result:
            self.game_result = self.VICTORY if self.team_id == self.game.winner_id else self.DEFEAT

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


from apps.common.enums import PlayerRole  # reuse player role enum for per-game stats

class PlayerGameStat(TimeStampedModel, UserStampedModel):
    game = models.ForeignKey(Game, related_name='player_stats', on_delete=models.CASCADE)
    team_stat = models.ForeignKey(TeamGameStat, related_name='player_stats', on_delete=models.CASCADE)
    player = models.ForeignKey('players.Player', related_name='game_stats', on_delete=models.CASCADE)

    team = models.ForeignKey(Team, related_name='player_game_stats', on_delete=models.CASCADE)

    role = models.CharField(
        max_length=10,
        choices=PlayerRole.choices,
        db_index=True,
        help_text="Role played in this match (Gold, Mid, Jungle, EXP, Roam)",
    )

    is_MVP = models.BooleanField(
        default=False,
        help_text="Indicates if the player was the MVP of the game"
    )

    hero = models.ForeignKey(Hero, on_delete=models.PROTECT)

    k = models.PositiveSmallIntegerField(default=0, help_text="Kills")
    d = models.PositiveSmallIntegerField(default=0, help_text="Deaths")
    a = models.PositiveSmallIntegerField(default=0, help_text="Assists")
    gold = models.PositiveIntegerField(default=0, help_text="Total Gold Earned")
    dmg_dealt = models.PositiveIntegerField(default=0, help_text="Total Damage Dealt")
    dmg_taken = models.PositiveIntegerField(default=0, help_text="Total Damage Taken")

    class Meta:
        unique_together = ('game', 'player')
        ordering = ['game', 'team', 'role']
        verbose_name = 'Player Game Stat'
        verbose_name_plural = 'Player Game Stats'
        indexes = [
            models.Index(fields=['role']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'player'],
                name='unique_player_stat_per_game',
                deferrable=models.Deferrable.DEFERRED
            ),
        ]

    def __str__(self):
        return f"{self.player.ign} Stats - {self.game}"

    def clean(self):
        super().clean()
        errors = {}

        # Ensure team_stat belongs to same game
        if self.team_stat and self.game and self.team_stat.game_id != self.game_id:
            errors['team_stat'] = "TeamGameStat must belong to the same game as PlayerGameStat."

        # Ensure self.team matches team_stat.team
        if self.team_stat and self.team and self.team_stat.team_id != self.team_id:
            errors['team'] = "Team must match the team in TeamGameStat."

        # Ensure the team is actually in the game
        if self.game and self.team_id not in [self.game.blue_side_id, self.game.red_side_id]:
            errors['team'] = "Team must be one of the teams in the game."

        # Ensure player was on that team on that game day
        if self.player_id and self.team_id and hasattr(self.game, 'series'):
            game_day = getattr(self.game.series, 'scheduled_date', None)
            if callable(game_day):
                # you had: getattr(..., 'scheduled_date', 'date', lambda: None)()
                # simplifying here:
                game_day = self.game.series.scheduled_date
            game_day = getattr(game_day, 'date', lambda: None)()

            memberships = self.player.memberships.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=game_day),
                start_date__lte=game_day,
            ).values_list('team_id', flat=True)

            if self.team_id not in memberships:
                errors['player'] = "Player must be a member of the team on the game day."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto-fill team from team_stat if missing
        if self.team_stat and not self.team_id:
            self.team = self.team_stat.team
        self.full_clean()
        super().save(*args, **kwargs)

    # --- rate properties ---
    @property
    def minutes(self) -> Decimal:
        game = self.game if hasattr(self, 'game') else self.team_stat.game
        dur = getattr(game, 'duration', None)
        if not dur:
            return Decimal(1)
        minutes = Decimal(dur.total_seconds()) / Decimal(60)
        return minutes if minutes > 0 else Decimal(1)

    @property
    def kda_rate(self) -> Decimal:
        deaths = Decimal(self.d or 0)
        denom = deaths if deaths > 0 else Decimal(1)
        val = (Decimal(self.k or 0) + Decimal(self.a or 0)) / denom
        return val.quantize(Decimal('0.01'))

    @property
    def gpm(self) -> Decimal:
        val = Decimal(self.gold or 0) / self.minutes
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def dpm(self) -> Decimal:
        val = Decimal(self.dmg_dealt or 0) / self.minutes
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class GameDraftAction(TimeStampedModel, UserStampedModel):
    game = models.ForeignKey(Game, related_name='draft_actions', on_delete=models.CASCADE)

    action = models.CharField(
        max_length=10,
        choices=[('BAN', 'Ban'), ('PICK', 'Pick')],
    )

    side = models.CharField(
        max_length=5,
        choices=Side.choices,
        db_index=True,
    )

    order = models.PositiveIntegerField(
        help_text="Order of the action in the draft, e.g., 1 for first action"
    )

    hero = models.ForeignKey(Hero, on_delete=models.PROTECT)

    player = models.ForeignKey(
        'players.Player',
        related_name='draft_actions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Set only for PICK actions; leave null for BAN actions"
    )

    team = models.ForeignKey(
        Team,
        related_name='draft_actions',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('game', 'order')
        ordering = ['game', 'order']
        verbose_name = 'Game Draft Action'
        verbose_name_plural = 'Game Draft Actions'
        indexes = [
            models.Index(fields=['game', 'order']),
            models.Index(fields=['game', 'side', 'order']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'order'],
                name='unique_draft_action_order_per_game',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(action__in=['BAN', 'PICK']),
                name='valid_action_value'
            ),
            models.CheckConstraint(
                check=Q(side__in=[Side.BLUE, Side.RED]),
                name='valid_side_value_draft'
            ),
        ]

    def __str__(self):
        return f'{self.game} - {self.action} {self.hero} ({self.side})'

    def _expected_team_id(self):
        if not self.game_id:
            return None
        return self.game.blue_side_id if self.side == Side.BLUE else self.game.red_side_id

    def clean(self):
        super().clean()

        errors = {}

        # Need game and side first
        if not self.game_id or not self.side:
            if not self.game_id:
                errors['game'] = "Game must be set before setting team."
            if not self.side:
                errors['side'] = "Side must be set before setting team."
            if errors:
                raise ValidationError(errors)
            return

        # Team on that side must be one of the series teams
        expected_team_id = self._expected_team_id()
        series_teams_ids = {self.game.series.team1_id, self.game.series.team2_id}
        if expected_team_id not in series_teams_ids:
            errors['team'] = "Team for the draft action must be one of the teams in the series."

        # BAN rules
        if self.action == 'BAN':
            if self.player_id:
                errors['player'] = "Player must be null for BAN actions."
            if not self.hero_id:
                errors['hero'] = "Hero must be set for BAN actions."

        # PICK rules
        elif self.action == 'PICK':
            if not self.player_id:
                errors['player'] = "Player must be set for PICK actions."
            if not self.hero_id:
                errors['hero'] = "Hero must be set for PICK actions."

        # player must belong to the correct team on game day
        if self.action == 'PICK' and self.player_id and expected_team_id:
            game_day = self.game.series.scheduled_date.date()
            memberships = self.player.memberships.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=game_day),
                start_date__lte=game_day,
            ).values_list('team_id', flat=True)
            if expected_team_id not in memberships:
                errors['player'] = "Player must be a member of the side's team on the game day."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)