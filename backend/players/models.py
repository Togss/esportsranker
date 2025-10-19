from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from common.models import TimeStampedModel, SluggedModel
from teams.models import Team
from datetime import date

ROLE_CHOICES = [
    ('GOLD', 'Gold Lane'),
    ('MID', 'Mid Lane'),
    ('JUNGLE', 'Jungle'),
    ('EXP', 'Exp Lane'),
    ('ROAM', 'Roam'),
]

def player_photo_upload_to(instance, filename: str) -> str:
    ext = f'.{filename.rsplit(".", 1)[-1].lower()}' if "." in filename else ""
    return f'player/photos/{instance.slug}{ext}'

IGN_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9_.\-]{2,24}$",
    message="In-Game Name must be 2-24 characters long and can include letters, numbers, underscores, hyphens, and periods."
)

class Player(TimeStampedModel, SluggedModel ):
    ign = models.CharField(max_length=24, unique=True, validators=[IGN_VALIDATOR, MinLengthValidator(2)])
    real_name = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to=player_photo_upload_to, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=2, blank=True, help_text="ISO 3166-1 alpha-2 country code")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Indicates if the player is currently active")
    achievements = models.TextField(blank=True)

    x = models.URLField(blank=True, help_text="Link to player's X (formerly Twitter) profile")
    facebook = models.URLField(blank=True, help_text="Link to player's Facebook profile")
    instagram = models.URLField(blank=True, help_text="Link to player's Instagram profile")
    youtube = models.URLField(blank=True, help_text="Link to player's YouTube channel")

    class Meta:
        ordering = ['ign']
        indexes = [
            models.Index(fields=['ign']),
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
    
class PlayerMembership(TimeStampedModel):
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    role_at_team = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently active with the team")
    is_starter = models.BooleanField(default=False, help_text="Indicates if the player was a starter during this membership")

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['team', 'start_date']),
            models.Index(fields=['player', 'start_date']),
        ]
        unique_together = ('player', 'team', 'start_date')

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        
        overlapping = PlayerMembership.objects.filter(
            player=self.player,
        ).exclude(pk=self.pk)
        for m in overlapping:
            a_start, a_end = self.start_date, self.end_date or date.max
            b_start, b_end = m.start_date, m.end_date or date.max
            if a_start <= b_end and b_start <= a_end:
                raise ValidationError("This membership period overlaps with another membership for the same player.")
            
    def __str__(self):
        end_display = self.end_date or "present"
        return f"{self.player.ign} - {self.team.short_name} ({self.start_date} to {end_display})"
    
    @property
    def is_active_today(self):
        today = date.today()
        end = self.end_date or today
        return self.start_date <= today <= end