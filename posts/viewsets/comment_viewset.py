from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from posts.models.comment import Comment
from posts.serializers.comment_serializer import CommentSerializer
from posts.services.feed_cache import invalidate_feed_for_author_and_followers
from posts.services.moderation import check_toxicity
from social_media.permissions import IsOwnerOrReadOnly


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = (
            Comment.objects.select_related("author", "author__profile", "post")
            .filter(post__is_active=True)
            .order_by("created_at")
        )
        post_id = self.request.query_params.get("post_id")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        check_toxicity(serializer.validated_data.get("content", ""))
        comment = serializer.save(author=self.request.user)
        invalidate_feed_for_author_and_followers(comment.post.author_id)

    def perform_destroy(self, instance):
        post_author_id = instance.post.author_id
        instance.delete()
        invalidate_feed_for_author_and_followers(post_author_id)
