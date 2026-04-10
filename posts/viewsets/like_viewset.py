from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from posts.models.like import Like
from posts.models.post import Post
from django.shortcuts import get_object_or_404
from posts.services.feed_cache import invalidate_feed_for_author_and_followers


class LikeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="toggle/(?P<post_id>[0-9]+)")
    def toggle(self, request, post_id=None, **kwargs):
        post = get_object_or_404(Post, id=post_id, is_active=True)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
        invalidate_feed_for_author_and_followers(post.author_id)
        likes_count = (
            Post.objects.filter(pk=post.pk)
            .annotate(_count=Count("likes"))
            .values_list("_count", flat=True)
            .first()
        ) or 0
        return Response(
            {"status": "liked" if created else "unliked", "likes_count": likes_count},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
