from django.db import models
from django.db.models import Q, F, Sum
from django.db.models.functions import Coalesce
import django.db.models as dj_models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from common.models import TimeStampedModel, SluggedModel
from teams.models import Team
from heroes.models import Hero
from decimal import Decimal, ROUND_HALF_UP
from common.slug_helper import ensure_unique_slug, build_stage_slug_base

class TournamentTeam(models.Model):
    INVITED = "INVITED"
    QUALIFIED = "QUALIFIED"
    FRANCHISE = "FRANCHISE"
    KIND_CHOICES = [
        (INVITED, "Invited"),
        (QUALIFIED, "Qualified"),
        (FRANCHISE, "Franchise"),
    ]

    tournament = models.ForeignKey(
        "competitions.Tournament",
        on_delete=models.CASCADE,
        related_name="tournament_teams"
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="tournament_entries"
    )
    seed = models.PositiveSmallIntegerField(blank=True, null=True)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, blank=True)
    group = models.CharField(max_length=16, blank=True, help_text="e.g., Group A")
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["seed", "team__short_name"]
        constraints = [
            models.UniqueConstraint(fields=["tournament", "team"], name="unique_tournament_team"),
        ]

    def __str__(self):
        return f"{self.team.short_name} ({self.tournament.name})"

TIER_CHOICES = [
    ('S', 'S-tier'),
    ('A', 'A-tier'),
    ('B', 'B-tier'),
    ('C', 'C-tier'),
    ('D', 'D-tier'),
]

STATUS_CHOICES = [
    ('UPCOMING', 'Upcoming'),
    ('ONGOING', 'Ongoing'),
    ('COMPLETED', 'Completed'),
]

def tournament_logo_upload_to(instance, filename: str) -> str:
    ext = f'.{filename.rsplit(".", 1)[-1].lower()}' if '.' in filename else ''
    return f'tournament/logos/{instance.slug}{ext}'

class Tournament(SluggedModel, TimeStampedModel):
    region = models.CharField(max_length=5, choices=Team._meta.get_field('region').choices, db_index=True)
    tier = models.CharField(max_length=2, choices=TIER_CHOICES, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, db_index=True)
    teams = models.ManyToManyField('teams.Team', through='competitions.TournamentTeam', related_name='tournaments', blank=True, help_text="Teams participating in the tournament")
    prize_pool = models.PositiveIntegerField(blank=True, null=True, help_text="Prize pool in USD")
    logo = models.ImageField(upload_to=tournament_logo_upload_to, blank=True, null=True)
    description = models.TextField(blank=True)
    tournament_rules_link = models.URLField(blank=True, help_text="Link to the tournament rules")

    class Meta:
        ordering = ['-start_date', 'name']
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['tier']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['region', 'status']),
            models.Index(fields=['tier', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        constraints = [
            models.CheckConstraint(check=~Q(slug=''), name='tournament_slug_not_empty'),
            models.UniqueConstraint(
                fields=['name', 'start_date'],
                name='unique_tournament_name_start_date',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F('start_date')),
                name='end_date_after_start_date'
            ),

        ]

    def compute_status(self):
        today = timezone.localdate()
        if self.start_date and self.end_date:
            if today < self.start_date:
                return 'UPCOMING'
            elif self.start_date <= today <= self.end_date:
                return 'ONGOING'
            else:
                return 'COMPLETED'
        return 'UPCOMING'
    
    def save(self, *args, **kwargs):
        self.status = self.compute_status()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


STAGE_TYPES = [
    ('WILD CARD', 'Wild Card Stage'),
    ('GROUPS', 'Group Stage'),
    ('REGULAR SEASON', 'Regular Season'),
    ('KNOCKOUTS', 'Knockout Stage'),
    ('PLAYOFFS', 'Playoffs Stage'),
    ('FINALS', 'Grand Finals'),
]

TIER_STAGE_CHOICES = [
    ('1', 'Tier 1'),
    ('2', 'Tier 2'),
    ('3', 'Tier 3'),
    ('4', 'Tier 4'),
    ('5', 'Tier 5'),
]
class Stage(TimeStampedModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='stages')
    stage_type = models.CharField(max_length=20, choices=STAGE_TYPES, db_index=True)
    slug = models.SlugField(max_length=50, blank=True, unique=True)
    variant = models.CharField(max_length=50, blank=True, help_text="Variant of the stage, e.g., 'Double Elimination'")
    order = models.PositiveIntegerField(help_text="Order of the stage in the tournament")
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    tier = models.CharField(max_length=2, choices=TIER_STAGE_CHOICES, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, db_index=True)

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
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F('start_date')),
                name='stage_end_date_after_start_date'
            ),
            models.UniqueConstraint(
                fields=['tournament', 'order'],
                name='unique_stage_order_per_tournament',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(order__gte=1),
                name='stage_order_gte_1'
            ),
        ]

    def __str__(self):
        type_label = dict(STAGE_TYPES).get(self.stage_type, self.stage_type.title())
        return f'{type_label}{f" - {self.variant}" if self.variant else ""} ({self.tournament.name})'

    def clean(self):
        super().clean()

        if not self.tournament_id:
            raise ValidationError("Tournament must be set for the stage.")
        
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after or equal to start date.")
        t = self.tournament
        if (t.start_date and self.start_date and self.start_date < t.start_date) or \
           (t.end_date and self.end_date and self.end_date > t.end_date):
            raise ValidationError("Stage dates must be within the tournament dates.")
        
    def compute_status(self):
        today = timezone.localdate()
        if self.start_date and self.end_date:
            if today < self.start_date:
                return 'UPCOMING'
            elif self.start_date <= today <= self.end_date:
                return 'ONGOING'
            else:
                return 'COMPLETED'
        return 'UPCOMING'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = build_stage_slug_base(self)
            candidate = base
        else:
            candidate = self.slug
        self.slug = ensure_unique_slug(candidate, self.__class__, instance_pk=self.pk)
        self.status = self.compute_status()
        self.full_clean()
        super().save(*args, **kwargs)


class Series(TimeStampedModel):
    tournament = models.ForeignKey(Tournament, related_name='series', on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, related_name='series', on_delete=models.CASCADE)
    team1 = models.ForeignKey(Team, related_name='series_as_team1', on_delete=models.CASCADE)
    team2 = models.ForeignKey(Team, related_name='series_as_team2', on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, related_name='series_won', on_delete=models.SET_NULL, null=True, blank=True)
    best_of = models.PositiveIntegerField(choices=[(1, 'Bo1'), (3, 'Bo3'), (5, 'Bo5'), (7, 'Bo7')], default=3)
    scheduled_date = models.DateTimeField(db_index=True)
    score = models.CharField(max_length=20, blank=True, help_text="Score in format 'Team1Score-Team2Score', e.g., '2-1'")

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Series'
        verbose_name_plural = 'Series'
        indexes = [
            models.Index(fields=['tournament']),
            models.Index(fields=['stage']),
            models.Index(fields=['team1']),
            models.Index(fields=['team2']),
            models.Index(fields=['winner']),
            models.Index(fields=['scheduled_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['stage', 'team1', 'team2'],
                name='unique_series_per_stage_teams',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=~Q(team1=F('team2')),
                name='teams_must_be_different_in_series'
            ),
        ]

    def __str__(self):
        return f"{self.team1.short_name} vs {self.team2.short_name} - {self.stage}"

    def compute_score_and_winner(self, persist: bool = True):
        from .services import compute_series_score_and_winner
        score_str, winner = compute_series_score_and_winner(self)

        if persist and (self.score != score_str or self.winner.id != (winner.id if winner else None)):
            type(self).objects.filter(pk=self.pk).update(score=score_str, winner=winner)
            self.score = score_str
            self.winner = winner

        return score_str, winner

    def clean(self):
        errors = {}
        if not self.tournament_id:
            errors['tournament'] = "Tournament must be set for the series."
        if not self.stage_id:
            errors['stage'] = "Stage must be set for the series."
        elif self.stage.tournament_id and self.stage.tournament_id != self.tournament_id:
            errors['stage'] = "Stage must belong to the same tournament as the series."

        if self.team1_id and self.team2_id and self.team1_id == self.team2_id:
            errors['team2'] = "Team 2 must be different from Team 1."

        if errors:
            raise ValidationError(errors)
        super().clean()

# Game model
# ----------------------------------------------------
# Stores individual game information within a series
# ----------------------------------------------------
class Game(TimeStampedModel):
    RESULT_CHOICES = [
        ('NORMAL', 'Normal Win'),
        ('FORFEIT_TEAM1', 'Forfeit - Team 1 Wins'),
        ('FORFEIT_TEAM2', 'Forfeit - Team 2 Wins'),
        ('NO_CONTEST', 'No Contest / Cancelled'),
    ]
    series = models.ForeignKey(Series, related_name='games', on_delete=models.CASCADE)
    game_no = models.PositiveIntegerField(help_text="Game number in the series, e.g., 1 for Game 1")
    blue_side = models.ForeignKey(Team, related_name='games_as_blue_side', on_delete=models.CASCADE)
    red_side = models.ForeignKey(Team, related_name='games_as_red_side', on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.DurationField(null=True, blank=True, help_text="Duration of the game")
    vod_link = models.URLField(blank=True, help_text="Link to the VOD of the game")
    result_type = models.CharField(max_length=20, choices=RESULT_CHOICES, default='NORMAL')

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
        if team_id := getattr(team, 'id', team):
            if team_id == self.blue_side_id:
                return 'BLUE'
            elif team_id == self.red_side_id:
                return 'RED'
        return 'None'

    def clean(self):
        super().clean()
        errors = {}

        # Ensure we have a series before deeper checks (admin create flow)
        if not self.series_id:
            if self.blue_side_id and self.red_side_id or self.winner_id:
                errors['series'] = "Series must be set before setting sides or winner."
                if errors:
                    raise ValidationError(errors)
            return
        
        # Blue/Red must be one of the series teams
        series_teams_ids = {self.series.team1_id, self.series.team2_id}
        if self.blue_side_id and self.blue_side_id not in series_teams_ids:
            errors['blue_side'] = "Blue side team must be one of the teams in the series."
        if self.red_side_id and self.red_side_id not in series_teams_ids:
            errors['red_side'] = "Red side team must be one of the teams in the series."
        
        # Winner (if set) must be either blue or red
        if self.winner_id is not None and self.winner_id not in {self.blue_side_id, self.red_side_id}:
            errors['winner'] = "Winner must be either the blue side or red side team."

        # Blue and Red must be different (db constraint will catch this too)
        if self.blue_side_id and self.red_side_id and self.blue_side_id == self.red_side_id:
            errors['red_side'] = "Red Side team must be different from Blue Side team."

        # game_no within best_of range
        if self.game_no is not None and getattr(self.series, 'best_of', None):
            if not (1 <= self.game_no <= self.series.best_of):
                errors['game_no'] = f"Game number must be between 1 and {self.series.best_of} for this series."
        if errors:
            raise ValidationError(errors)
        
    def save(self, *args, **kwargs):
        is_creating = self._state.adding
        # Derive winner from result_type if applicable
        if self.result_type == 'FORFEIT_TEAM1':
            self.winner = self.series.team1
        elif self.result_type == 'FORFEIT_TEAM2':
            self.winner = self.series.team2
        elif self.result_type == 'NO_CONTEST':
            self.winner = None
        
        self.full_clean()
        super().save(*args, **kwargs)

        # Ensure TeamGameStat rows exist for both sides once created
        if is_creating and self.blue_side_id and self.red_side_id:
            def _ensure_team_stats():
                TeamGameStat.objects.get_or_create(
                    game=self,
                    team_id=self.blue_side_id,
                    defaults={'side': 'BLUE'}
                )
                TeamGameStat.objects.get_or_create(
                    game=self,
                    team_id=self.red_side_id,
                    defaults={'side': 'RED'}
                )
            transaction.on_commit(_ensure_team_stats)


# TeamGameStat model
# ----------------------------------------------------
# Stores team statistics for each game
# ----------------------------------------------------
class TeamGameStat(TimeStampedModel):
    BLUE = 'BLUE'
    RED = 'RED' 
    SIDE_CHOICES = [
        (BLUE, 'Blue'),
        (RED, 'Red'),
    ]
    VICTORY = 'VICTORY'
    DEFEAT = 'DEFEAT'
    RESULT_CHOICES = [
        (VICTORY, 'Win'),
        (DEFEAT, 'Loss'),
    ]
    game = models.ForeignKey(Game, related_name='team_stats', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='game_stats', on_delete=models.CASCADE)
    side = models.CharField(max_length=5, choices=SIDE_CHOICES, db_index=True)

    tower_destroyed = models.PositiveSmallIntegerField(default=0)
    lord_kills = models.PositiveSmallIntegerField(default=0)
    turtle_kills = models.PositiveSmallIntegerField(default=0)
    orange_buff = models.PositiveSmallIntegerField(default=0, help_text="Number of Orange Buffs secured")
    purple_buff = models.PositiveSmallIntegerField(default=0, help_text="Number of Purple Buffs secured")
    game_result = models.CharField(max_length=7, choices=RESULT_CHOICES, blank=True, help_text="Result of the game for the team")
    gold = models.PositiveIntegerField(default=0, help_text="Total Gold Earned by the team")
    score = models.PositiveSmallIntegerField(default=0, help_text="Total Team Score")

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
    
    def __repr__(self):
        return f"<TeamGameStat: {self.team.short_name} - Game {self.game.game_no} ({self.game.series})>"

    def clean(self):
        super().clean()
        errors = {}

        # Validate that the team is part of the game
        if self.team_id not in [self.game.blue_side_id, self.game.red_side_id]:
            errors['team'] = "Team must be one of the teams in the game."
        # Derive expected side from (game, team)
        if self.team_id == self.game.blue_side_id:
            expected_side = self.BLUE
        elif self.team_id == self.game.red_side_id:
            expected_side = self.RED
        else:
            expected_side = None
        if expected_side and self.side and self.side != expected_side:
            errors['side'] = f"Side must be '{expected_side}' for the selected team."
        # Error if two teams input the same game_result
        if self.game.team_stats.exclude(pk=self.pk).filter(game_result=self.game_result).exists():
            errors['game_result'] = "Another team already has this game result for the same game."
        if errors:
            raise ValidationError(errors)
        # Soft auto-fill (so admin forms 'just work')
        # Note: doing this in clean() is acceptable; alternatively do it in save().
        if expected_side and not self.side:
            self.side = expected_side
        if self.game.winner_id is not None and not self.game_result:
            self.game_result = 'VICTORY' if self.team_id == self.game.winner_id else 'DEFEAT'

    def save(self, *args, **kwargs):
        # Ensure clean is called before saving
        self.full_clean()
        return super().save(*args, **kwargs)
    
    
# PlayerGameStat model
# ----------------------------------------------------
# Stores individual player statistics for each game
# ----------------------------------------------------    
ROLE_CHOICES = [
    ('GOLD', 'Gold Lane'),
    ('MID', 'Mid Lane'),
    ('JUNGLE', 'Jungle'),
    ('EXP', 'Exp Lane'),
    ('ROAM', 'Roam'),
]  

class PlayerGameStat(TimeStampedModel):
    game = models.ForeignKey(Game, related_name='player_stats', on_delete=models.CASCADE)
    team_stat = models.ForeignKey(TeamGameStat, related_name='player_stats', on_delete=models.CASCADE)
    player = models.ForeignKey('players.Player', related_name='game_stats', on_delete=models.CASCADE)

    team = models.ForeignKey(Team, related_name='player_game_stats', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    is_MVP = models.BooleanField(default=False, help_text="Indicates if the player was the MVP of the game")

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
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'player'],
                name='unique_player_stat_per_game',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(role__in=[choice[0] for choice in ROLE_CHOICES]),
                name='valid_role_value'
            ),
        ]
    def __str__(self):
        return f"{self.player.ign} Stats - {self.game}"

    def clean(self):
        super().clean()
        errors = {}

        # Ensure team_stat belongs to the same game
        if self.team_stat and self.game and self.team_stat.game_id != self.game_id:
            errors['team_stat'] = "TeamGameStat must belong to the same game as PlayerGameStat."
        
        # Ensure team matches team_stat
        if self.team_stat and self.team and self.team_stat.team_id != self.team_id:
            errors['team'] = "Team must match the team in TeamGameStat."

        # Ensure team belongs to the game
        if self.game and self.team_id not in [self.game.blue_side_id, self.game.red_side_id]:
            errors['team'] = "Team must be one of the teams in the game."
        
        # Ensure player is a member of the team on the game day
        if self.player_id and self.team_id and hasattr(self.game, 'series'):
            game_day = getattr(self.game.series, 'scheduled_date', 'date', lambda: None)()
            memberships = self.player.team_memberships.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=game_day),
                start_date__lte=game_day,
            ).values_list('team_id', flat=True)
            if self.team_id not in memberships:
                errors['player'] = "Player must be a member of the team on the game day."

        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Auto-fill team from team_stat if not set
        if self.team_stat and not self.team_id:
            self.team = self.team_stat.team
        self.full_clean()
        super().save(*args, **kwargs)
        
    @property
    def minutes(self) -> Decimal:
        # Game duration in minutes
        game = self.game if hasattr(self, 'game') else self.team_stat.game
        dur = getattr(game, 'duration', None)
        if not dur:
            return Decimal(1)
        minutes = Decimal(dur.total_seconds()) / Decimal(60)
        return minutes if minutes > 0 else Decimal(1)

    @property
    def kda_rate(self) -> Decimal:
        deaths = Decimal(self.deaths or 0)
        denom = deaths if deaths > 0 else Decimal(1)
        val = (Decimal(self.kills or 0) + Decimal(self.assists or 0)) / denom
        return val.quantize(Decimal('0.01'))
    
    @property
    def gpm(self) -> Decimal:
        val = Decimal(self.gold or 0) / self.minutes
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @property
    def dpm(self) -> Decimal:
        val = Decimal(self.dmg_dealt or 0) / self.minutes
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# GameDraftAction model
# ----------------------------------------------------
# Stores draft actions (bans/picks) for each game
# ----------------------------------------------------
class GameDraftAction(TimeStampedModel):
    game = models.ForeignKey(Game, related_name='draft_actions', on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=[('BAN', 'Ban'), ('PICK', 'Pick')])
    side = models.CharField(max_length=5, choices=[('BLUE', 'Blue'), ('RED', 'Red')], db_index=True)
    order = models.PositiveIntegerField(help_text="Order of the action in the draft, e.g., 1 for first action")
    hero = models.ForeignKey(Hero, on_delete=models.PROTECT)

    player = models.ForeignKey('players.Player', related_name='draft_actions', on_delete=models.SET_NULL, null=True, blank=True, help_text="Set only for PICK actions; leave null for BAN actions")
    team = models.ForeignKey(Team, related_name='draft_actions', on_delete=models.CASCADE)

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
                check=Q(side__in=['BLUE', 'RED']),
                name='valid_side_value_draft'
            ),
        ]

    def __str__(self):
        side = self.side
        return f'{self.game} - {self.action} {self.hero} ({side})'

    def _expected_team_id(self):
        if not self.game_id:
            return None
        return self.game.blue_side_id if self.side == 'BLUE' else self.game.red_side_id
    
    def clean(self):
        super().clean()
    
        errors = {}

        # Need game and side selected first
        if not self.game_id or not self.side:
            if not self.game_id:
                errors['game'] = "Game must be set before setting team."
            if not self.side:
                errors['side'] = "Side must be set before setting team."
            if errors:
                raise ValidationError(errors)
            return
        
        # Validate the side/team belongs to the series
        series_teams_ids = {self.game.series.team1_id, self.game.series.team2_id}
        expected_team_id = self._expected_team_id()
        if expected_team_id not in series_teams_ids:
            errors['team'] = "Team for the draft action must be one of the teams in the series."

        # Field requirements based on action type
        if self.action == 'BAN':
            if self.player_id:
                errors['player'] = "Player must be null for BAN actions."
            if not self.hero_id:
                errors['hero'] = "Hero must be set for BAN actions."
        elif self.action == 'PICK':
            if not self.player_id:
                errors['player'] = "Player must be set for PICK actions."
            if not self.hero_id:
                errors['hero'] = "Hero must be set for PICK actions."

        # Ensure the player (when set) is a member of the that side's team on the game day
        if self.action == 'PICK' and self.player_id and expected_team_id and hasattr(self.game, 'series', 'scheduled_date'):
            game_day = self.game.series.scheduled_date.date()
            memberships = self.player.team_memberships.filter(
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