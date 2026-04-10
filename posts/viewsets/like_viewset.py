from django.db import IntegrityError
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
        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            liked = False
        except Like.DoesNotExist:
            try:
                Like.objects.create(user=request.user, post=post)
                liked = True
            except IntegrityError:
                liked = True
        invalidate_feed_for_author_and_followers(post.author_id)
        likes_count = post.likes.count()
        return Response(
            {"status": "liked" if liked else "unliked", "likes_count": likes_count},
            status=status.HTTP_201_CREATED if liked else status.HTTP_200_OK,
        )
