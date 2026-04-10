from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from accounts.views import home_view
from social_media.views import healthcheck

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("", include("accounts.urls")),
    path("antisocial/v1/", include("accounts.api_urls")),
    path("antisocial/v1/", include("posts.api_urls")),
    path("", include("posts.urls")),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    path("health/", healthcheck, name="healthcheck"),
    path("robots.txt", static_serve, {"document_root": settings.STATICFILES_DIRS[0], "path": "robots.txt"}, name="robots_txt"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
