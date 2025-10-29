import factory
from django.utils import timezone
from apps.competitions.models import (
    Tournament,
    TournamentTeam,
    Stage,
    Series,
    Game,
    TeamGameStat,
)
from apps.teams.tests.factories import TeamFactory
from apps.common.enums import Region, TournamentTier, TournamentStatus, StageType, StageTier, StageStatus, Side, SeriesLength, GameResultType


# === Tournament ===
class TournamentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tournament

    name = factory.Sequence(lambda n: f"MPL PH Season {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))  # ✅ add this line
    region = Region.PH
    tier = TournamentTier.S
    start_date = factory.LazyFunction(lambda: timezone.localdate() - timezone.timedelta(days=5))
    end_date = factory.LazyFunction(lambda: timezone.localdate() + timezone.timedelta(days=5))
    status = TournamentStatus.ONGOING
    prize_pool = 100000
    description = "Sample tournament for testing"
    rules_link = "https://example.com/rules"

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for team in extracted:
                TournamentTeam.objects.create(tournament=self, team=team)
        else:
            t1 = TeamFactory()
            t2 = TeamFactory()
            TournamentTeam.objects.create(tournament=self, team=t1)
            TournamentTeam.objects.create(tournament=self, team=t2)


# === Stage ===
class StageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stage

    tournament = factory.SubFactory(TournamentFactory)
    stage_type = StageType.GROUP
    variant = "Group A"
    order = 1
    start_date = factory.LazyAttribute(lambda o: o.tournament.start_date)
    end_date = factory.LazyAttribute(lambda o: o.tournament.end_date)
    tier = StageTier.T1
    status = StageStatus.ONGOING


# === Series ===
class SeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Series

    tournament = factory.SubFactory(TournamentFactory)
    stage = factory.SubFactory(StageFactory, tournament=factory.SelfAttribute("..tournament"))
    team1 = factory.LazyAttribute(lambda o: o.tournament.tournament_teams.first().team)
    team2 = factory.LazyAttribute(lambda o: o.tournament.tournament_teams.last().team)
    scheduled_date = factory.LazyFunction(timezone.now)
    best_of = SeriesLength.BO3


# === Game ===
class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    series = factory.SubFactory(SeriesFactory)
    game_no = 1
    blue_side = factory.LazyAttribute(lambda o: o.series.team1)
    red_side = factory.LazyAttribute(lambda o: o.series.team2)
    duration = factory.LazyFunction(lambda: timezone.timedelta(minutes=18))
    vod_link = "https://example.com/vod"
    result_type = GameResultType.NORMAL


# === TeamGameStat ===
class TeamGameStatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamGameStat

    game = factory.SubFactory(GameFactory)
    team = factory.LazyAttribute(lambda o: o.game.blue_side)
    side = Side.BLUE
    tower_destroyed = 5
    lord_kills = 1
    turtle_kills = 2
    orange_buff = 3
    purple_buff = 3
    game_result = "VICTORY"
    gold = 65000
    t_score = 25