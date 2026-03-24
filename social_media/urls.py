from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

from accounts.views import home_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("", include("accounts.urls")),
    re_path(r"antisocial/(?P<version>(v1|v2))/", include("accounts.api_urls")),
    re_path(r"antisocial/(?P<version>(v1|v2))/", include("posts.api_urls")),
    path("", include("posts.urls")),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
