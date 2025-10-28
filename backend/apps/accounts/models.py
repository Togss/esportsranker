from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    MODERATOR = 'MODERATOR', _('Moderator')
    REVIEWER = 'REVIEWER', _('Reviewer')

class User(AbstractUser, TimeStampedModel):
    role = models.CharField(
        max_length=28,
        choices=UserRole.choices,
        default=UserRole.REVIEWER,
        db_index=True,
    )

    def display_role(self) -> str:
        return self.get_role_display()

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_moderator(self) -> bool:
        return self.role == UserRole.MODERATOR

    def is_reviewer(self) -> bool:
        return self.role == UserRole.REVIEWER
    
    class Meta:
        ordering = ['username']
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.role})"