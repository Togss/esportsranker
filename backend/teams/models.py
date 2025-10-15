from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator
from common.models import TimeStampedModel, SluggedModel

REGION_CHOICES = [
    ('NA', 'North America'),
    ('ID', 'Indonesia'),
    ('MY', 'Malaysia'),
    ('PH', 'Philippines'),
    ('SG', 'Singapore'),
    ('BR', 'Brazil'),
    ('VN', 'Vietnam'),
    ('MM', 'Myanmar'),
    ('TH', 'Thailand'),
    ('IN', 'India'),
    ('TR', 'Turkey'),
    ('EU', 'Europe'),
    ('KR', 'Korea'),
    ('TW', 'Taiwan'),
    ('HK', 'Hong Kong'),
    ('JP', 'Japan'),
    ('CN', 'China'),
    ('MENA', 'Middle East and North Africa'),
    ('LATAM', 'Latin America'),
    ('INTL', 'International'),
    ('WORLD', 'World'),
]

SHORT_NAME_VALIDATOR = RegexValidator(
    regex=r'^[A-Z0-9]{2,10}$',
    message='Short name must be 2-10 characters long, containing only uppercase letters and numbers.'
)

class Team(SluggedModel, TimeStampedModel):
    short_name = models.CharField(max_length=10, unique=True, validators=[SHORT_NAME_VALIDATOR, MinLengthValidator(2)])
    region = models.CharField(max_length=5, choices=REGION_CHOICES)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    achievements = models.TextField(blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    social_media_links = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-founded_year', 'name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['is_active']),
            models.Index(fields=['founded_year']),
            models.Index(fields=['region', 'is_active'])
        ]
        constraints = [
            models.CheckConstraint(check=~models.Q(slug=''), name='team_slug_not_empty'),
            models.CheckConstraint(
                check=Q(founded_year__isnull=True) | (Q(founded_year__gte=1850) & Q(founded_year__lte=2100)),
                name='founded_year_valid_range'
            )
        ]

    def __str__(self):
        return f"{self.short_name} ({self.region})"
