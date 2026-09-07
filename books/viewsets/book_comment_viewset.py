from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from books.models.book_comment import BookComment
from books.serializers.book_comment_serializer import BookCommentSerializer
from posts.services.moderation import check_toxicity
from social_media.permissions import IsOwnerOrReadOnly


class BookCommentViewSet(viewsets.ModelViewSet):
    serializer_class = BookCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = (
            BookComment.objects.select_related("author", "author__profile", "book")
            .order_by("created_at")
        )
        book_id = self.request.query_params.get("book_id")
        if book_id is not None:
            if not book_id.isdigit():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"book_id": "Must be a valid integer."})
            queryset = queryset.filter(book_id=book_id)
        return queryset

    def perform_create(self, serializer):
        check_toxicity(serializer.validated_data.get("content", ""))
        serializer.save(author=self.request.user)
