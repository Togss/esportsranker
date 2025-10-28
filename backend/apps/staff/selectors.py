from datetime import date
from django.db.models import Q, Prefetch
from .models import Staff, StaffMembership

def get_staff_by_team(team_id: str, active_only: bool = True):
    today = date.today()

    memberships_q = StaffMembership.objects.filter(team_id=team_id)

    if active_only:
        memberships_q = memberships_q.filter(
            (Q(end_date__isnull=True) | Q(end_date__gte=today)),
            start_date__lte=today,
        )

    return (
        Staff.objects.filter(
            memberships__in=memberships_q
        )
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=StaffMembership.objects.filter(team_id=team_id).order_by("-start_date"),
                to_attr="filtered_memberships",  # we can expose this in serializer if we want
            )
        )
        .order_by("handle")
        .distinct()
    )

def search_staff(
        query: str | None = None,
        role: str | None = None,
        nationality: str | None = None,
        active_only: bool | None = None,
):
    qs = Staff.objects.all()

    # fuzzy search by handle or full name (SluggedModel.name)
    if query:
        qs = qs.filter(
            Q(handle__icontains=query)
            | Q(name__icontains=query)
        )

    # filter by role
    if role:
        qs = qs.filter(primary_role=role)

    # filter by nationality
    if nationality:
        qs = qs.filter(nationality__iexact=nationality)

    # filter by active status
    if active_only:
        qs = qs.filter(is_active=active_only)

    return (
        qs
        .prefetch_related(
            "memberships",
            queryset=StaffMembership.objects.select_related("team")
            .order_by("-start_date"),
        )
        .only(
            "id",
            "handle",
            "name",
            "slug",
            "primary_role",
            "nationality",
            "is_active",
            "photo",
            "created_at",
            "updated_at",
        )
    )