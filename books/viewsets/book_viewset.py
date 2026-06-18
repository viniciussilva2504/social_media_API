from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from books.models.book import Book
from books.serializers.book_serializer import BookSerializer
from social_media.permissions import IsOwnerOrReadOnly


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = (
            Book.objects.filter(is_available=True)
            .select_related("owner", "owner__profile")
            .annotate(trade_requests_count=Count("trade_requests", distinct=True))
            .order_by("-created_at")
        )
        username = self.request.query_params.get("username")
        if username:
            qs = qs.filter(owner__username=username)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
