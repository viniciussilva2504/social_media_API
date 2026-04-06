from django.db.models import Count, Exists, OuterRef
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from posts.models.like import Like
from posts.models.post import Post
from posts.serializers.post_serializer import PostSerializer
from posts.services.feed_cache import invalidate_feed_for_author_and_followers
from posts.services.moderation import check_toxicity
from social_media.permissions import IsOwnerOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = (
            Post.objects.filter(is_active=True)
            .select_related("author", "author__profile")
            .annotate(
                _likes_count=Count("likes", distinct=True),
                _comments_count=Count("comments", distinct=True),
            )
            .order_by("-created_at")
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                _is_liked=Exists(
                    Like.objects.filter(
                        user=self.request.user, post=OuterRef("pk")
                    )
                )
            )
        return queryset

    def perform_create(self, serializer):
        check_toxicity(serializer.validated_data.get("content", ""))
        post = serializer.save(author=self.request.user)
        invalidate_feed_for_author_and_followers(post.author_id)

    def perform_update(self, serializer):
        post = serializer.save()
        invalidate_feed_for_author_and_followers(post.author_id)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        invalidate_feed_for_author_and_followers(instance.author_id)
