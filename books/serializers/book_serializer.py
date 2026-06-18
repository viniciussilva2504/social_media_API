from rest_framework import serializers

from books.models.book import Book


class BookSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_display_name = serializers.CharField(source="owner.profile.display_name", read_only=True)
    trade_requests_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Book
        fields = [
            "id",
            "owner_username",
            "owner_display_name",
            "title",
            "book_author",
            "description",
            "cover",
            "is_available",
            "trade_requests_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
