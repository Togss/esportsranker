from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HeroViewSet

router = DefaultRouter()
router.register("heroes", HeroViewSet, basename="hero")

urlpatterns = [
    path("", include(router.urls)),
]