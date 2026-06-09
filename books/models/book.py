from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User


def validate_cover_size(file):
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        from django.core.exceptions import ValidationError
        raise ValidationError("Cover image must be under 5MB.")


class Book(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="books")
    title = models.CharField(max_length=200)
    book_author = models.CharField(max_length=200)
    description = models.TextField(max_length=500, blank=True)
    cover = models.ImageField(
        upload_to="book_covers/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_cover_size,
        ],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["is_available", "-created_at"]),
        ]

    def __str__(self):
        return f'"{self.title}" — @{self.owner.username}'
