from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth', include('apps.accounts.urls')),  # JWT auth endpoints

    # Public API (v1)
    path('api/v1/', include('apps.api.urls')),  # All public endpoints centralized here

    # Moderator/desktop ingestion API
    path('ingest/', include('apps.ingest.urls')),

    # API Schema and Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)