from datetime import date
from django.db import models
from django.db.models import Q

from apps.common.models import (
    TimeStampedModel,
    SluggedModel,
    UserStampedModel,
)
from apps.common.enums import StaffRole
from apps.common.validators import (
        NATIONALITY_VALIDATOR,
        validate_start_before_end,
        validate_membership_overlap,
)
from apps.teams.models import Team


def staff_photo_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return f"staff/photos/{instance.slug}.{ext}" if ext else f"staff/photos/{instance.slug}"

class Staff(TimeStampedModel, SluggedModel, UserStampedModel):
    # SluggedModel gives: name (real / display), slug
    handle = models.CharField(
        max_length=24,
        unique=True,
        db_index=True,
        help_text="Public alias / coach tag (e.g. BONCHAN, MASTERCOACH).",
    )

    photo = models.ImageField(upload_to=staff_photo_upload_to, blank=True, null=True)

    primary_role = models.CharField(
        max_length=20,
        choices=StaffRole.choices,
        db_index=True,
        help_text="Main role overall (head coach, analyst, etc.)",
    )

    nationality = models.CharField(
        max_length=2,
        blank=True,
        db_index=True,
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


class StaffMembership(TimeStampedModel, UserStampedModel):
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
        choices=StaffRole.choices,
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
        validate_start_before_end(
            self.start_date,
            self.end_date,
            field_start='start_date',
            field_end='end_date'
        )

        validate_membership_overlap(
            subject=self.staff,
            start_date=self.start_date,
            end_date=self.end_date,
            current_pk=self.pk,
            queryset=StaffMembership.objects,
            subject_field_name='staff',
            overlap_error_message='This staff member already has an active contract in that time range.'
        )

    def __str__(self):
        end_display = self.end_date or 'present'
        return f"{self.staff.handle} – {self.team.short_name} ({self.start_date} to {end_display})"

    @property
    def is_active_today(self):
        today = date.today()
        end = self.end_date or today
        return self.start_date <= today <= end