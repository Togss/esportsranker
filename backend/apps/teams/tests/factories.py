import factory
from factory import Faker
from apps.teams.models import Team
from apps.common.enums import Region


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Faker("company")
    short_name = factory.Sequence(lambda n: f"TEAM{n}")
    region = Region.PH

    founded_year = 2020
    is_active = True
    achievements = Faker("sentence", nb_words=6)
    description = Faker("paragraph", nb_sentences=2)

    website = "https://example.org"
    x = "https://x.com/example"
    facebook = "https://facebook.com/example"
    youtube = "https://youtube.com/@example"