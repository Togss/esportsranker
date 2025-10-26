from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

from apps.common.enums import PlayerRole
from apps.common.validators import (
    NATIONALITY_VALIDATOR,
    validate_start_before_end,
    validate_membership_overlap
)
from apps.common.models import TimeStampedModel, SluggedModel
from apps.teams.models import Team


def player_photo_upload_to(instance, filename: str) -> str:
    ext = f'.{filename.rsplit(".", 1)[-1].lower()}' if "." in filename else ""
    return f'player/photos/{instance.slug}{ext}'

#--------------------------------------------------------------------
# Player Model and PlayerMembership Model
#--------------------------------------------------------------------
class Player(TimeStampedModel, SluggedModel ):
    ign = models.CharField(
        max_length=30,
        unique=True,
        help_text="In-Game Name (IGN) of the player",
        db_index=True
    )
    photo = models.ImageField(upload_to=player_photo_upload_to, blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=PlayerRole.choices,
        db_index=True
    )

    date_of_birth = models.DateField(blank=True, null=True)

    nationality = models.CharField(
        max_length=2, blank=True,
        help_text="ISO 3166-1 alpha-2 country code"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates if the player is currently active"
    )

    achievements = models.TextField(blank=True)

    x = models.URLField(blank=True, help_text="Link to player's X (formerly Twitter) profile")
    facebook = models.URLField(blank=True, help_text="Link to player's Facebook profile")
    instagram = models.URLField(blank=True, help_text="Link to player's Instagram profile")
    youtube = models.URLField(blank=True, help_text="Link to player's YouTube channel")

    class Meta:
        ordering = ['ign']
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['nationality']),
        ]
        constraints = [
            models.CheckConstraint(
                name='player_slug_not_empty',
                check=~models.Q(slug='')
            ),
        ]

    def __str__(self):
        return self.ign
    
    def clean(self):
        if self.nationality:
            self.nationality = self.nationality.upper()
            NATIONALITY_VALIDATOR(self.nationality)

    @property
    def age(self) -> int | None:
        if not self.date_of_birth:
            return None
        today = date.today()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years

class PlayerMembership(TimeStampedModel):
    player = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE,
        related_name='memberships'
    )
    role_at_team = models.CharField(
        max_length=10,
        choices=PlayerRole.choices,
        db_index=True,
        help_text="Player's primary role while at the team"
    )

    start_date = models.DateField()
    end_date = models.DateField(
        blank=True, null=True,
        help_text="Leave blank if currently active with the team"
    )

    is_starter = models.BooleanField(
        default=False,
        help_text="Indicates if the player was a starter during this membership"
    )

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['team', 'start_date']),
            models.Index(fields=['player', 'start_date']),
        ]
        unique_together = ('player', 'team', 'start_date')

    def clean(self):
        validate_start_before_end(
            self.start_date,
            self.end_date,
            field_start='start_date',
            field_end='end_date'
        )
        validate_membership_overlap(
            subject=self.player,
            start_date=self.start_date,
            end_date=self.end_date,
            current_pk=self.pk,
            queryset=PlayerMembership.objects,
            subject_field_name='player',
            overlap_error_message='This player has overlapping team memberships.'
        )

    def __str__(self):
        end_display = self.end_date or 'present'
        return f"{self.player.ign} - {self.team.short_name} ({self.start_date} to {end_display})"
    
    @property
    def is_active_today(self):
        today = date.today()
        end = self.end_date or today
        return self.start_date <= today <= end
