from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from books.models.book import Book
from books.serializers.book_serializer import BookSerializer
from social_media.permissions import IsOwnerOrReadOnly


class IsBookOwnerOrReadOnly(IsOwnerOrReadOnly):
    # Book's ownership field is `owner`, not the shared permission's
    # default `author`/`user` — without this override, has_object_permission
    # always falls through to None == request.user (False), so nobody,
    # not even the owner, could ever update or delete a Book via the API.
    owner_field = "owner"


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsBookOwnerOrReadOnly]

    def get_queryset(self):
        qs = (
            Book.objects.select_related("owner", "owner__profile")
            .annotate(trade_requests_count=Count("trade_requests", distinct=True))
            .order_by("-created_at")
        )
        # Only the listing hides unavailable books — retrieve/update/destroy
        # must still reach a book that's unavailable, otherwise its owner
        # loses API access to it (e.g. to toggle it back to available)
        # the moment it stops being available.
        if self.action == "list":
            qs = qs.filter(is_available=True)
            username = self.request.query_params.get("username")
            if username:
                qs = qs.filter(owner__username=username)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
