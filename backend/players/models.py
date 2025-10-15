from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator
from common.models import TimeStampedModel
from teams.models import Team

ROLE_CHOICES = [
    ('GOLD', 'Gold Lane'),
    ('MID', 'Mid Lane'),
    ('JUNGLE', 'Jungle'),
    ('EXP', 'Exp Lane'),
    ('ROAM', 'Roam'),
]

IGN_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9_.\-]{2,24}$",
    message="In-Game Name must be 2-24 characters long and can include letters, numbers, underscores, hyphens, and periods."
)

class Player(TimeStampedModel):
    ign = models.CharField(max_length=24, unique=True, validators=[IGN_VALIDATOR, MinLengthValidator(2)])
    real_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='players', db_index=True)
    nationality = models.CharField(max_length=2, blank=True, help_text="ISO 3166-1 alpha-2 country code")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Indicates if the player is currently active")
    achievements = models.TextField(blank=True)

    class Meta:
        ordering = ['-is_active', 'team__name', 'role', 'ign']
        verbose_name = 'Player'
        verbose_name_plural = 'Players'
        indexes = [
            models.Index(fields=['team', 'role']),
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['ign']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['team', 'ign'], name='unique_team_ign', deferrable=models.Deferrable.DEFERRED),
        ]

    def __str__(self) -> str:
        return f"{self.ign} ({self.team.short_name if self.team else 'No Team'})"