from rest_framework import serializers

from posts.models.comment import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(
        source="author.profile.display_name", read_only=True
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_username",
            "author_display_name",
            "post",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "author_username", "author_display_name", "created_at"]
