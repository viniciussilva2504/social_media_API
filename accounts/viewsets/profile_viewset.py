from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User

from accounts.models.profile import Profile
from accounts.serializers.profile_serializer import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    UserSearchSerializer,
)
from social_media.permissions import IsProfileOwner


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "username"
    lookup_value_regex = r"[\w.@+-]+"
    permission_classes = [IsProfileOwner]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated(), IsProfileOwner()]

    def get_queryset(self):
        return (
            Profile.objects.select_related("user")
            .annotate(
                _followers_count=Count("user__followers", distinct=True),
                _following_count=Count("user__following", distinct=True),
            )
            .order_by("id")
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_object(self):
        if self.kwargs.get("username") == "me":
            if not self.request.user.is_authenticated:
                from rest_framework.exceptions import NotAuthenticated
                raise NotAuthenticated()
            self.kwargs["username"] = self.request.user.username
        return super().get_object()


class UserSearchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.select_related("profile").all()
        q = self.request.query_params.get("q", "")
        if q:
            queryset = queryset.filter(username__icontains=q)
        return queryset.order_by("username")
