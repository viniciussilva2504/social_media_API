from django.db import models
from django.contrib.auth.models import User

from books.models.book import Book


class TradeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="trade_requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_trade_requests")
    offered_book = models.CharField(max_length=200)
    message = models.TextField(max_length=280, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # One pending request per requester per book
        constraints = [
            models.UniqueConstraint(
                fields=["book", "requester"],
                condition=models.Q(status="pending"),
                name="unique_pending_trade_per_user_per_book",
            )
        ]

    def __str__(self):
        return f"@{self.requester.username} → \"{self.book.title}\" (offers: {self.offered_book})"
