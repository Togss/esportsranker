from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel, SluggedModel

CLASS_CHOICES = [
    ('TANK', 'Tank'),
    ('FIGHTER', 'Fighter'),
    ('ASSASSIN', 'Assassin'),
    ('MAGE', 'Mage'),
    ('MARKSMAN', 'Marksman'),
    ('SUPPORT', 'Support'),
]

def hero_icon_upload_to(instance, filename: str) -> str:
    ext = f'.{filename.rsplit(".", 1)[-1].lower()}' if "." in filename else ""
    return f'heroes/icons/{instance.slug}{ext}'

class Hero(SluggedModel, TimeStampedModel):
    primary_class = models.CharField(max_length=20, choices=CLASS_CHOICES, db_index=True)
    secondary_class = models.CharField(max_length=20, choices=CLASS_CHOICES, blank=True, null=True)
    hero_icon = models.ImageField(upload_to=hero_icon_upload_to, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Hero'
        verbose_name_plural = 'Heroes'
        indexes = [
            models.Index(fields=['primary_class']),
            models.Index(fields=['name']),
        ]
        constraints = [
            models.CheckConstraint(check=~models.Q(slug=''), name='hero_slug_not_empty'),
        ]

    def clean(self):
        if self.secondary_class and self.secondary_class == self.primary_class:
            raise ValidationError("Secondary class must be different from primary class.")

    def __str__(self) -> str:
        return self.name
    
    @property
    def classes(self) -> list[str]:
        labels = dict(CLASS_CHOICES)
        out = [labels.get(self.primary_class)]
        if self.secondary_class:
            out.append(labels.get(self.secondary_class))
        return [x for x in out if x]