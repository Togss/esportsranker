from django.db.models import Q
from .models import Team

def search_teams(
        query: str | None = None,
        region: str | None = None,
        is_active: bool | None = None,
):
    qs = Team.objects.all()

    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(short_name__icontains=query) |
            Q(description__icontains=query)
        )

    if region:
        qs = qs.filter(region=region)

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    return (
        qs.select_related()
        .only(
            "id",
            "name",
            "slug",
            "short_name",
            "region",
            "is_active",
            "logo",
            "created_at",
            "updated_at",
        )
        .order_by("short_name")
    )