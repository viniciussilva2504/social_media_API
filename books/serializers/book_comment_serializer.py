from rest_framework import serializers

from books.models.book_comment import BookComment


class BookCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(
        source="author.profile.display_name", read_only=True
    )

    class Meta:
        model = BookComment
        fields = [
            "id",
            "author_username",
            "author_display_name",
            "book",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "author_username", "author_display_name", "created_at"]
        extra_kwargs = {
            "book": {"required": True},
        }
