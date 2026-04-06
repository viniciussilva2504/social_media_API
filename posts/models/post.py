from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(max_length=280)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return f"@{self.author.username}: {self.content[:50]}"

    @property
    def likes_count(self):
        if hasattr(self, "_likes_count"):
            return self._likes_count
        return self.likes.count()

    @property
    def comments_count(self):
        if hasattr(self, "_comments_count"):
            return self._comments_count
        return self.comments.count()
