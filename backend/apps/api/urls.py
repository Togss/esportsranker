from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.api.auth_views import WhoAmIView
from apps.api.jwt_views import EsportsTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    TeamViewSet,
    PlayerViewSet,
    HeroViewSet,
    StaffViewSet,
    TournamentViewSet,
    StageViewSet,
    SeriesViewSet,
    GameViewSet,
    TeamGameStatViewSet,
    PlayerGameStatViewSet,
    GameDraftActionViewSet
)

# We'll register viewsets on this router later
app_name = "api"

router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'heroes', HeroViewSet, basename='hero')
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'tournaments', TournamentViewSet, basename='tournament')
router.register(r'stages', StageViewSet, basename='stage')
router.register(r'series', SeriesViewSet, basename='series')
router.register(r'games', GameViewSet, basename='game')
router.register(r'team-game-stats', TeamGameStatViewSet, basename='teamgamestat')
router.register(r'player-game-stats', PlayerGameStatViewSet, basename='playergamestat')
router.register(r'game-draft-actions', GameDraftActionViewSet, basename='gamedraftaction')


urlpatterns = [
    # core resource endpoints
    path("", include(router.urls)),

    # auth / identity endpoints
    path("auth/whoami/", WhoAmIView.as_view(), name="whoami"),

    path("auth/token/", EsportsTokenObtainPairView.as_view(), name="token_obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]