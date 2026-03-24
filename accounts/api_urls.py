from django.urls import include, path
from rest_framework import routers

from accounts import viewsets

router = routers.DefaultRouter()
router.register(r"register", viewsets.RegisterViewSet, basename="register")
router.register(r"login", viewsets.LoginViewSet, basename="login")
router.register(r"profile", viewsets.ProfileViewSet, basename="profile")
router.register(r"users", viewsets.UserSearchViewSet, basename="users")
router.register(r"follow", viewsets.FollowViewSet, basename="follow")

urlpatterns = [
    path("", include(router.urls)),
]
