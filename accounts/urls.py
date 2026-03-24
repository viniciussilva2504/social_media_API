from django.urls import path
from accounts.views import (
    login_view,
    register_view,
    logout_view,
    profile_view,
    edit_profile_view,
    followers_view,
    following_view,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("profile/<str:username>/", profile_view, name="profile"),
    path("profile/<str:username>/edit/", edit_profile_view, name="edit_profile"),
    path("profile/<str:username>/followers/", followers_view, name="followers"),
    path("profile/<str:username>/following/", following_view, name="following"),
]
