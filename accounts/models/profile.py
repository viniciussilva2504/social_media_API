from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User


def validate_profile_picture_size(file):
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        from django.core.exceptions import ValidationError
        raise ValidationError("Profile picture must be under 5MB.")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True, db_index=True)
    bio = models.TextField(max_length=280, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_profile_picture_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.user.username}"

    @property
    def followers_count(self):
        if hasattr(self, "_followers_count"):
            return self._followers_count
        return self.user.followers.count()

    @property
    def following_count(self):
        if hasattr(self, "_following_count"):
            return self._following_count
        return self.user.following.count()
