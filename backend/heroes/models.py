from django.db import models
from common.models import TimeStampedModel, SluggedModel

class Hero(SluggedModel, TimeStampedModel):
    hero_class = models.CharField(max_length=50, unique=True)
    hero_pic = models.ImageField(upload_to='hero_pictures/', blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Hero'
        verbose_name_plural = 'Heroes'
        indexes = [
            models.Index(fields=['hero_class']),
            models.Index(fields=['name']),
        ]
        constraints = [
            models.CheckConstraint(check=~models.Q(slug=''), name='hero_slug_not_empty'),
        ]

    def __str__(self) -> str:
        return self.name