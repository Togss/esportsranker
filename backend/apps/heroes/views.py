from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Hero
from .serializers import HeroSerializer

class HeroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public, read-only endpoint for all MLBB heroes.
    """
    queryset = Hero.objects.all().only(
        "id", "name", "slug",
        "primary_class", "secondary_class", "hero_icon",
        "created_at", "updated_at"
    )
    serializer_class = HeroSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["primary_class", "secondary_class"]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]