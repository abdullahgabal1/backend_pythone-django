"""
Daary AI Backend — Root URL Configuration
==========================================
All API endpoints live under /api/v1/ and are namespaced by app.
Developer dashboard endpoints live under /api/v1/developer/.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# ─── Buyer-facing API ────────────────────────────────────────────
api_v1_patterns = [
    path("auth/", include("apps.authentication.urls")),
    path("account/", include("apps.users.urls")),
    path("properties/", include("apps.properties.urls")),
    path("favorites/", include("apps.favorites.urls")),
    path("inquiries/", include("apps.inquiries.urls")),
    path("ai/", include("apps.ai.urls")),
    path("search/", include("apps.search.urls")),
    path("locations/", include("apps.locations.urls")),
    path("contact/", include("apps.marketing.urls")),
    # Developer dashboard
    path("developer/", include("apps.developer_accounts.urls")),
    path("developer/", include("apps.projects.urls")),
    path("developer/", include("apps.dashboard.urls")),
]

# ─── API Documentation ──────────────────────────────────────────
docs_patterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns = [
    path("health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/docs/", include(docs_patterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
