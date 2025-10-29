from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.response import Response
from rest_framework.views import APIView


# ---------
# YAML schema view for older drf-spectacular
# (Some versions don't allow passing media_type into as_view)
# ---------
class SpectacularYAMLView(APIView):
    """
    Return the same OpenAPI schema as /api/schema/,
    but rendered as YAML for freeze-tagging in git.
    """
    def get(self, request, *args, **kwargs):
        # call SpectacularAPIView's underlying generator
        schema_view = SpectacularAPIView()
        schema_response = schema_view.get(request, *args, **kwargs)

        # schema_response.data is the OpenAPI dict
        from drf_spectacular.renderers import OpenApiYamlRenderer
        renderer = OpenApiYamlRenderer()

        yaml_bytes = renderer.render(schema_response.data, renderer_context={})
        return Response(
            yaml_bytes.decode("utf-8"),
            content_type="application/x-yaml",
        )


urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Auth / Accounts (JWT issue/refresh/etc.)
    path("api/auth/", include("apps.accounts.urls")),

    # Public Read API (consumed by the website / frontend)
    # v1 is schema-frozen and documented
    path("api/v1/", include(("apps.api.urls", "api"), namespace="v1")),

    # Secure Data Entry / Ingest API
    # Used by internal desktop tooling (admins, moderators)
    path("ingest/", include("apps.ingest.urls")),

    # OpenAPI schema (machine-readable JSON)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema-json"),

    # OpenAPI schema (YAML, for tagging in git / freeze snapshots)
    path("api/schema.yaml", SpectacularYAMLView.as_view(), name="schema-yaml"),

    # Interactive API docs (Swagger-style, good for dev & QA)
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema-json"),
        name="swagger-ui",
    ),

    # Read-only reference docs (Redoc-style, good for sharing)
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema-json"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)