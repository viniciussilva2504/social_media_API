from django.contrib import admin
from django.db.models import Count

from posts.models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["author", "content", "created_at", "get_likes_count", "get_comments_count", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["author__username", "content"]
    list_select_related = ["author"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _likes_count=Count("likes", distinct=True),
                _comments_count=Count("comments", distinct=True),
            )
        )

    @admin.display(description="Likes", ordering="_likes_count")
    def get_likes_count(self, obj):
        return obj._likes_count

    @admin.display(description="Comments", ordering="_comments_count")
    def get_comments_count(self, obj):
        return obj._comments_count


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    list_select_related = ["user", "post"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "post", "content", "created_at"]
    list_select_related = ["author", "post"]
