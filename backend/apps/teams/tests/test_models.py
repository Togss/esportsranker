import pytest
from apps.teams.models import Team
from apps.teams.tests.factories import TeamFactory


@pytest.mark.django_db
def test_team_factory_creates_team_successfully():
    team = TeamFactory()

    # sanity: object is created
    assert isinstance(team, Team)

    # sanity: db row exists
    assert Team.objects.count() == 1

    # required constraints look correct
    assert team.short_name is not None
    assert team.region == "PH" or team.region == team.region.upper()

    # boolean default logic didn't flip
    assert team.is_active is True

    # slug should exist because of SluggedModel
    assert getattr(team, "slug", None)