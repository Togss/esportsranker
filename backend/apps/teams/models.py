from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator
from apps.common.models import TimeStampedModel, SluggedModel, UserStampedModel
from apps.common.enums import Region
from apps.common.validators import TEAM_SHORT_NAME_VALIDATOR

def team_logo_upload_to(instance, filename):
    ext = f'.{filename.rsplit(".", 1)[-1].lower()}' if "." in filename else ""
    base = (instance.slug or instance.name).lower().replace(" ", "_")
    return f'team_logos/{base}{ext}' if ext else f'team_logos/{base}'

class Team(SluggedModel, TimeStampedModel, UserStampedModel):
    short_name = models.CharField(
        max_length=10,
        unique=True,
        validators=[TEAM_SHORT_NAME_VALIDATOR, MinLengthValidator(2)],
        help_text='Abbreviated team name (2-10 uppercase letters/numbers).',
        db_index=True,
    )

    region = models.CharField(
        max_length=5,
        choices=Region.choices,
        help_text='Select the region the team belongs to.',
        db_index=True,
    )
    
    logo = models.ImageField(upload_to=team_logo_upload_to, blank=True, null=True)
    achievements = models.TextField(blank=True)

    founded_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1850),
            MaxValueValidator(2100)
        ],
        help_text='Year the team was founded (between 1850 and 2100).'
    )

    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    website = models.URLField(blank=True)
    x = models.URLField(blank=True, verbose_name='Twitter URL')
    facebook = models.URLField(blank=True, verbose_name='Facebook URL')
    youtube = models.URLField(blank=True, verbose_name='YouTube URL')

    class Meta:
        ordering = ['short_name']
        indexes = [
            models.Index(fields=['region', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['short_name'],
                name='unique_team_short_name_ci_unique',
            ),
            models.CheckConstraint(
                name='founded_year_valid_range',
                check=Q(founded_year__gte=1850, founded_year__lte=2100) | Q(founded_year__isnull=True)
            ), 
        ]

    def __str__(self):
        return f"{self.short_name}"
