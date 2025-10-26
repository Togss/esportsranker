from django.urls import path
from .views import (
    SeriesIngestView,
    GameResultIngestView,
)

app_name = "ingest"

urlpatterns = [
    path("series/", SeriesIngestView.as_view(), name="series-ingest"),
    path("game-result/", GameResultIngestView.as_view(), name="game-result-ingest"),
]