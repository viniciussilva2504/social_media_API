from django.db.models import Count, Exists, OuterRef
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from posts.models.like import Like
from posts.models.post import Post
from posts.serializers.post_serializer import PostSerializer
from accounts.models.follow import Follow
from posts.services.feed_cache import (
    build_feed_response_cache_key,
    get_feed_cache_timeout,
)


class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(
            follower=user
        ).values_list("following_id", flat=True)
        from django.db.models import Q
        return (
            Post.objects.filter(
                Q(author_id__in=following_ids) | Q(author=user),
                is_active=True,
            )
            .select_related("author", "author__profile")
            .annotate(
                _likes_count=Count("likes", distinct=True),
                _comments_count=Count("comments", distinct=True),
                _is_liked=Exists(
                    Like.objects.filter(user=user, post=OuterRef("pk"))
                ),
            )
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        cache_key = build_feed_response_cache_key(
            request.user.id,
            request.query_params.urlencode(),
        )
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=get_feed_cache_timeout())
        return response
