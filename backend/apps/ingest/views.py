from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    SeriesCreateSerializer,
    GameResultUpdateSerializer,
)


class SeriesIngestView(APIView):
    """
    POST /ingest/series/
    Intended for the desktop moderator app to submit a new Series.

    Current state (Week 1 Day 6):
    - We accept payload structure
    - We DON'T write to DB yet (no auth layer yet)
    """
    def post(self, request, *args, **kwargs):
        serializer = SeriesCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # We'll hook in competitions.services.create_series(...) here
        # after we add auth/permissions.
        return Response(
            {
                "detail": "Series ingest endpoint registered. Write logic not enabled yet."
            },
            status=status.HTTP_202_ACCEPTED,
        )


class GameResultIngestView(APIView):
    """
    POST /ingest/game-result/
    Intended to report final game info (sides, winner, result_type, duration).

    Same idea: shape is in place, write is not enabled yet.
    """
    def post(self, request, *args, **kwargs):
        serializer = GameResultUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Later:
        #   competitions.services.record_game_result(...)
        #   competitions.services.update_series_from_games(...)
        return Response(
            {
                "detail": "Game result ingest endpoint registered. Write logic not enabled yet."
            },
            status=status.HTTP_202_ACCEPTED,
        )