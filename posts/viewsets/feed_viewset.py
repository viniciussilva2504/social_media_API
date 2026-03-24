from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from posts.models.post import Post
from posts.serializers.post_serializer import PostSerializer
from accounts.models.follow import Follow


class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list("following_id", flat=True)
        feed_user_ids = list(following_ids) + [self.request.user.id]
        return (
            Post.objects.filter(author_id__in=feed_user_ids)
            .select_related("author", "author__profile")
            .order_by("-created_at")
        )
