# apps/players/selectors.py

from datetime import date
from django.db.models import Q, Prefetch
from .models import Player, PlayerMembership


def get_players_by_team(team_id: str, active_only: bool = True):
    today = date.today()

    memberships_q = PlayerMembership.objects.filter(team_id=team_id)

    if active_only:
        memberships_q = memberships_q.filter(
            (Q(end_date__isnull=True) | Q(end_date__gte=today)),
            start_date__lte=today,
        )

    qs = (
        Player.objects.filter(
            memberships__in=memberships_q
        )
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=PlayerMembership.objects.filter(team_id=team_id).order_by("-start_date"),
                to_attr="filtered_memberships",  # we can expose this in serializer if we want
            )
        )
        .order_by("ign")
        .distinct()
    )

    return qs

def search_players(
    query: str | None = None,
    role: str | None = None,
    nationality: str | None = None,
    active_only: bool | None = None,
):
    qs = Player.objects.all()

    # fuzzy search by IGN or full name (SluggedModel.name)
    if query:
        qs = qs.filter(
            Q(ign__icontains=query)
            | Q(name__icontains=query)
        )

    # filter by role
    if role:
        qs = qs.filter(role=role)

    # nationality is stored as uppercase ISO alpha-2
    if nationality:
        qs = qs.filter(nationality__iexact=nationality)

    # active_only -> is_active
    if active_only is not None:
        qs = qs.filter(is_active=active_only)

    return (
        qs.prefetch_related("memberships__team",)
        .only(
            "id",
            "ign",
            "name",
            "slug",
            "role",
            "nationality",
            "is_active",
            "photo",
            "created_at",
            "updated_at",
        )
    .order_by("ign")
    )