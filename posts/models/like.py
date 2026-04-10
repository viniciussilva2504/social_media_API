from django.db import models
from django.contrib.auth.models import User

from posts.models.post import Post


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_user_post_like"),
        ]
        indexes = [
            models.Index(fields=["post", "user"]),
        ]

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"
