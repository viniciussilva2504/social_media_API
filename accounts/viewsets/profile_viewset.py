from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User

from accounts.models.profile import Profile
from accounts.serializers.profile_serializer import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    UserSearchSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "username"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Profile.objects.select_related("user").all().order_by("id")

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_object(self):
        if self.kwargs.get("username") == "me":
            return self.request.user.profile
        return super().get_object()

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {"detail": "You can only edit your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {"detail": "You can only edit your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)


class UserSearchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.select_related("profile").all()
        q = self.request.query_params.get("q", "")
        if q:
            queryset = queryset.filter(username__icontains=q)
        return queryset.order_by("username")
