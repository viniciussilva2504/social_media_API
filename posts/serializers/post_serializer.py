from rest_framework import serializers

from posts.models.post import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(
        source="author.profile.display_name", read_only=True
    )
    author_profile_picture = serializers.ImageField(
        source="author.profile.profile_picture", read_only=True
    )
    likes_count = serializers.IntegerField(source="_likes_count", read_only=True, default=0)
    comments_count = serializers.IntegerField(source="_comments_count", read_only=True, default=0)
    is_liked = serializers.BooleanField(source="_is_liked", read_only=True, default=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "author_username",
            "author_display_name",
            "author_profile_picture",
            "content",
            "image",
            "likes_count",
            "comments_count",
            "is_liked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
