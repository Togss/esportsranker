from django.db import models
from django.db.models import Q, F
from common.models import TimeStampedModel, SluggedModel
from teams.models import Team
from heroes.models import Hero

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

class Tournament(SluggedModel, TimeStampedModel):
    region = models.CharField(max_length=5, choices=Team._meta.get_field('region').choices)
    tier = models.CharField(max_length=2, choices=TIER_CHOICES, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, db_index=True)
    teams = models.ManyToManyField(Team, related_name='tournaments', blank=True)
    prize_pool = models.PositiveIntegerField(blank=True, null=True, help_text="Prize pool in USD")
    logo = models.ImageField(upload_to='tournament_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    rules = models.TextField(blank=True)

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
    def __str__(self):
        return self.name
    

class Stage(TimeStampedModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='stages', db_index=True)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(help_text="Order of the stage in the tournament")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['tournament', 'order']
        verbose_name = 'Stage'
        verbose_name_plural = 'Stages'
        indexes = [
            models.Index(fields=['tournament', 'order']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'name'],
                name='unique_stage_name_per_tournament',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F('start_date')),
                name='stage_end_date_after_start_date'
            ),
        ]
    def __str__(self):
        return f"{self.tournament.name} - {self.name}"
    

class Series(TimeStampedModel):
    stage = models.ForeignKey(Stage, related_name='series', on_delete=models.CASCADE, db_index=True)
    team1 = models.ForeignKey(Team, related_name='series_as_team1', on_delete=models.CASCADE, db_index=True)
    team2 = models.ForeignKey(Team, related_name='series_as_team2', on_delete=models.CASCADE, db_index=True)
    winner = models.ForeignKey(Team, related_name='series_won', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    best_of = models.PositiveIntegerField(choices=[(1, 'Bo1'), (3, 'Bo3'), (5, 'Bo5'), (7, 'Bo7')], default=3)
    scheduled_date = models.DateTimeField(db_index=True)
    score = models.CharField(max_length=20, blank=True, help_text="Score in format 'Team1Score-Team2Score', e.g., '2-1'")

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Series'
        verbose_name_plural = 'Series'
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['team1']),
            models.Index(fields=['team2']),
            models.Index(fields=['winner']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['team1', 'team2']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['stage', 'team1', 'team2'],
                name='unique_series_per_stage',
                deferrable=models.Deferrable.DEFERRED
            ),
            models.CheckConstraint(
                check=~Q(team1=F('team2')),
                name='teams_must_be_different'
            ),
            models.CheckConstraint(
                check=Q(best_of__in=[1, 3, 5, 7]),
                name='valid_best_of_value'
            ),
        ]
    def __str__(self):
        return f"{self.team1.short_name} vs {self.team2.short_name} - {self.stage.name}"
    

class Game(TimeStampedModel):
    series = models.ForeignKey(Series, related_name='games', on_delete=models.CASCADE, db_index=True)
    game_no = models.PositiveIntegerField(help_text="Game number in the series, e.g., 1 for Game 1")
    blue_side = models.ForeignKey(Team, related_name='games_as_blue_side', on_delete=models.CASCADE, db_index=True)
    red_side = models.ForeignKey(Team, related_name='games_as_red_side', on_delete=models.CASCADE, db_index=True)
    winner = models.ForeignKey(Team, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    duration = models.DurationField(help_text="Duration of the game")
    vod_link = models.URLField(blank=True, help_text="Link to the VOD of the game")

    class Meta:
        unique_together = ('series', 'game_no')
        ordering = ['series', 'game_no']
        verbose_name = 'Game'
        verbose_name_plural = 'Games'
        indexes = [
            models.Index(fields=['series']),
            models.Index(fields=['blue_side']),
            models.Index(fields=['red_side']),
            models.Index(fields=['winner']),
            models.Index(fields=['game_no']),
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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.blue_side not in [self.series.team1, self.series.team2]:
            raise ValidationError("Blue side team must be one of the series teams.")
        if self.red_side not in [self.series.team1, self.series.team2]:
            raise ValidationError("Red side team must be one of the series teams.")
        if self.winner and self.winner not in [self.blue_side, self.red_side]:
            raise ValidationError("Winner must be either the blue side or red side team.")
        
        if self.blue_side_id == self.red_side_id:
            raise ValidationError("Blue side and Red side teams must be different.")
        pair = {self.series.team1_id, self.series.team2_id}
        if self.blue_side_id not in pair or self.red_side_id not in pair:
            raise ValidationError("Both teams must be part of the series.")
        if self.winner and self.winner_id not in pair:
            raise ValidationError("Winner must be one of the series teams.")
        if self.game_no < 1 or self.game_no > self.series.best_of:
            raise ValidationError(f"Game number must be between 1 and {self.series.best_of}.")
        super().clean()

    def __str__(self):
        return f"G{self.game_no} - {self.series}"
    

SIDE_CHOICES = [
    ('BLUE', 'Blue Side'),
    ('RED', 'Red Side'),
]

class TeamGameStat(TimeStampedModel):
    game = models.ForeignKey(Game, related_name='team_stats', on_delete=models.CASCADE, db_index=True)
    team = models.ForeignKey(Team, related_name='game_stats', on_delete=models.CASCADE, db_index=True)
    side = models.CharField(max_length=5, choices=SIDE_CHOICES, db_index=True)

    # aggregate stats
    k = models.PositiveIntegerField(default=0, help_text="Kills")
    d = models.PositiveIntegerField(default=0, help_text="Deaths")
    a = models.PositiveIntegerField(default=0, help_text="Assists")
    gold = models.PositiveIntegerField(default=0, help_text="Total Gold Earned")

    turret_kills = models.PositiveIntegerField(default=0)
    lord_kills = models.PositiveIntegerField(default=0)
    turtle_kills = models.PositiveIntegerField(default=0)
    first_blood = models.BooleanField(default=False)

    class Meta:
        unique_together = ('game', 'team')
        ordering = ['game', 'team']
        verbose_name = 'Team Game Stat'
        verbose_name_plural = 'Team Game Stats'
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['team']),
            models.Index(fields=['side']),
            models.Index(fields=['game', 'team']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'team'],
                name='unique_team_stat_per_game',
                deferrable=models.Deferrable.DEFERRED
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.team not in [self.game.blue_side, self.game.red_side]:
            raise ValidationError("Team must be one of the teams in the game.")
        expected_side = 'BLUE' if self.team == self.game.blue_side else 'RED'
        if self.side != expected_side:
            raise ValidationError(f"Side must be '{expected_side}' for the selected team.")
        super().clean()

    def __str__(self):
        return f"{self.team.short_name} Stats - {self.game}"

ROLE_CHOICES = [
    ('GOLD', 'Gold Lane'),
    ('MID', 'Mid Lane'),
    ('JUNGLE', 'Jungle'),
    ('EXP', 'Exp Lane'),
    ('ROAM', 'Roam'),
]  

class PlayerGameStat(TimeStampedModel):
    game = models.ForeignKey(Game, related_name='player_stats', on_delete=models.CASCADE, db_index=True)
    team_stat = models.ForeignKey(TeamGameStat, related_name='player_stats', on_delete=models.CASCADE, db_index=True)
    player = models.ForeignKey('players.Player', related_name='game_stats', on_delete=models.CASCADE, db_index=True)

    team = models.ForeignKey(Team, related_name='player_game_stats', on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    is_starter = models.BooleanField(default=True, help_text="Indicates if the player was a starter in the game")
    is_MVP = models.BooleanField(default=False, help_text="Indicates if the player was the MVP of the game")

    hero = models.CharField(max_length=50, help_text="Hero played by the player")

    k = models.PositiveIntegerField(default=0, help_text="Kills")
    d = models.PositiveIntegerField(default=0, help_text="Deaths")
    a = models.PositiveIntegerField(default=0, help_text="Assists")
    gold = models.PositiveIntegerField(default=0, help_text="Total Gold Earned")
    gpm = models.FloatField(default=0.0, help_text="Gold Per Minute")
    dmg_dealt = models.PositiveIntegerField(default=0, help_text="Total Damage Dealt")
    dmg_taken = models.PositiveIntegerField(default=0, help_text="Total Damage Taken")

    class Meta:
        unique_together = ('game', 'player')
        ordering = ['game', 'team', 'role']
        verbose_name = 'Player Game Stat'
        verbose_name_plural = 'Player Game Stats'
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['player']),
            models.Index(fields=['team']),
            models.Index(fields=['role']),
            models.Index(fields=['game', 'player']),
            models.Index(fields=['team', 'role']),
        ]
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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.player.team != self.team:
            raise ValidationError("Player must belong to the specified team.")
        if self.team_stat.team != self.team:
            raise ValidationError("Team in team_stat must match the specified team.")
        if self.team not in [self.game.blue_side, self.game.red_side]:
            raise ValidationError("Team must be one of the teams in the game.")
        super().clean()

    def __str__(self):
        return f"{self.player.ign} Stats - {self.game}"
    

class GameDraftAction(TimeStampedModel):
    game = models.ForeignKey(Game, related_name='draft_actions', on_delete=models.CASCADE, db_index=True)
    action = models.CharField(max_length=10, choices=[('BAN', 'Ban'), ('PICK', 'Pick')])
    side = models.CharField(max_length=5, choices=SIDE_CHOICES)
    order = models.PositiveIntegerField(help_text="Order of the action in the draft, e.g., 1 for first action")
    hero = models.ForeignKey(Hero, on_delete=models.PROTECT, db_index=True)

    player = models.ForeignKey('players.Player', related_name='draft_actions', on_delete=models.SET_NULL, null=True, blank=True, db_index=True, help_text="Set only for PICK actions; leave null for BAN actions")
    team = models.ForeignKey(Team, related_name='draft_actions', on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('game', 'order')
        ordering = ['game', 'order']
        verbose_name = 'Game Draft Action'
        verbose_name_plural = 'Game Draft Actions'
        indexes = [
            models.Index(fields=['game']),
            models.Index(fields=['team']),
            models.Index(fields=['side']),
            models.Index(fields=['action']),
            models.Index(fields=['hero']),
            models.Index(fields=['game', 'order']),
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
        return f"{self.game} - {self.get_action_display()} {self.hero.name} ({self.side})"