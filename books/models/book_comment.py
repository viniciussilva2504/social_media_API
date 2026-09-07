from django.db import models
from django.contrib.auth.models import User

from books.models.book import Book


class BookComment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_comments")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["book", "created_at"]),
        ]

    def __str__(self):
        return f"@{self.author.username} on book {self.book_id}: {self.content[:50]}"
