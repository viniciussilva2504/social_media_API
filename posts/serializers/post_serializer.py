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
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author_username",
            "author_display_name",
            "author_profile_picture",
            "content",
            "likes_count",
            "comments_count",
            "is_liked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
