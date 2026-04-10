from django.urls import path, re_path
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
    re_path(r"^profile/(?P<username>[\w.@+-]+)/$", profile_view, name="profile"),
    re_path(r"^profile/(?P<username>[\w.@+-]+)/edit/$", edit_profile_view, name="edit_profile"),
    re_path(r"^profile/(?P<username>[\w.@+-]+)/followers/$", followers_view, name="followers"),
    re_path(r"^profile/(?P<username>[\w.@+-]+)/following/$", following_view, name="following"),
]
