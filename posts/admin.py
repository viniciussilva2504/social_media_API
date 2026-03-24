from django.contrib import admin
from posts.models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["author", "content", "created_at", "likes_count", "comments_count"]
    search_fields = ["author__username", "content"]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "post", "content", "created_at"]
