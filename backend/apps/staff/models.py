from datetime import date
from django.db import models
from django.db.models import Q
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from apps.common.models import TimeStampedModel, SluggedModel
from apps.teams.models import Team

STAFF_ROLE_CHOICES = [
    ('HEAD_COACH', 'Head Coach'),
    ('ASST_COACH', 'Assistant Coach'),
    ('ANALYST', 'Analyst'),
    ('MANAGER', 'Team Manager'),
]

def staff_photo_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return f"staff/photos/{instance.slug}.{ext}" if ext else f"staff/photos/{instance.slug}"

HANDLE_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9_\-.]{2,24}$',
    message='Handle must be 2–24 characters and can include letters, numbers, underscores, hyphens, and periods.',
)

NATIONALITY_VALIDATOR = RegexValidator(
    regex=r'^[A-Z]{2}$',
    message='Nationality must be ISO 3166-1 alpha-2 (e.g., PH, ID, JP).',
)

class Staff(TimeStampedModel, SluggedModel):
    # SluggedModel gives: name (real / display), slug
    handle = models.CharField(
        max_length=24,
        unique=True,
        validators=[HANDLE_VALIDATOR],
        help_text="Public alias / coach tag (e.g. BONCHAN, MASTERCOACH).",
    )

    photo = models.ImageField(upload_to=staff_photo_upload_to, blank=True, null=True)

    primary_role = models.CharField(
        max_length=20,
        choices=STAFF_ROLE_CHOICES,
        db_index=True,
        help_text="Main role overall (head coach, analyst, etc.)",
    )

    nationality = models.CharField(
        max_length=2,
        blank=True,
        help_text="ISO 3166-1 alpha-2 code (e.g. PH)",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Is this staff member still active in the scene?",
    )

    bio = models.TextField(blank=True)
    achievements = models.TextField(blank=True)

    x = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)

    class Meta:
        ordering = ['handle']
        indexes = [
            models.Index(fields=['primary_role', 'is_active']),
            models.Index(fields=['nationality']),
        ]
        constraints = [
            models.CheckConstraint(
                name='staff_slug_not_empty',
                check=~Q(slug=''),
            ),
        ]

    def __str__(self):
        return self.handle

    def clean(self):
        if self.nationality:
            self.nationality = self.nationality.upper()
            NATIONALITY_VALIDATOR(self.nationality)


class StaffMembership(TimeStampedModel):
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='staff_memberships',
    )
    role_at_team = models.CharField(
        max_length=20,
        choices=STAFF_ROLE_CHOICES,
        db_index=True,
        help_text="Role held on this specific team during this period.",
    )

    start_date = models.DateField()
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Leave blank if still active with this team.",
    )

    class Meta:
        ordering = ('-start_date',)
        indexes = [
            models.Index(fields=['team', 'start_date']),
            models.Index(fields=['staff', 'start_date']),
        ]
        unique_together = (
            ('staff', 'team', 'start_date'),
        )

    def clean(self):
        # 0. If parent staff isn't saved yet, we can't meaningfully check overlaps.
        # This happens in admin when creating a new Staff + inline memberships together.
        if not self.staff_id:
            return

        # 1. Can't end before start.
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be earlier than start date.')

        # 2. Prevent overlapping contracts for the SAME STAFF across teams.
        overlapping = (
            StaffMembership.objects
            .filter(staff=self.staff)
            .exclude(pk=self.pk)
        )

        for m in overlapping:
            a_start = self.start_date
            a_end = self.end_date or date.max
            b_start = m.start_date
            b_end = m.end_date or date.max

            # ranges [a_start, a_end] and [b_start, b_end] overlap?
            if a_start <= b_end and b_start <= a_end:
                raise ValidationError(
                    'This staff member already has an active contract in that time range.'
                )

    def __str__(self):
        end_display = self.end_date or 'present'
        return f"{self.staff.handle} – {self.team.short_name} ({self.start_date} to {end_display})"

    @property
    def is_active_today(self):
        today = date.today()
        end = self.end_date or today
        return self.start_date <= today <= end