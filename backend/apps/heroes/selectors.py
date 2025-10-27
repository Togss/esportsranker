from django.db.models import Q
from .models import Hero

def search_heroes(
        query: str | None = None,
        hero_class: str | None = None
):
    qs = Hero.objects.all()

    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(slug__icontains=query)
        )

    if hero_class:
        qs = qs.filter(
            Q(primary_class=hero_class)
            | Q(secondary_class=hero_class)
        )

    return (
        qs.only(
            "id",
            "name",
            "slug",
            "primary_class",
            "secondary_class",
            "hero_icon",
            "created_at",
            "updated_at",
        )
        .order_by("name")
    )