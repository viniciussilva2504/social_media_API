from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from posts.models.like import Like
from posts.models.post import Post
from django.shortcuts import get_object_or_404


class LikeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="toggle/(?P<post_id>[0-9]+)")
    def toggle(self, request, post_id=None, **kwargs):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            return Response({"status": "unliked", "likes_count": post.likes_count})
        return Response(
            {"status": "liked", "likes_count": post.likes_count},
            status=status.HTTP_201_CREATED,
        )
