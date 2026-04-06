from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from PIL import Image, UnidentifiedImageError

from accounts.models.profile import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    followers_count = serializers.IntegerField(source="_followers_count", read_only=True, default=0)
    following_count = serializers.IntegerField(source="_following_count", read_only=True, default=0)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "display_name",
            "bio",
            "profile_picture",
            "followers_count",
            "following_count",
            "is_following",
            "created_at",
        ]
        read_only_fields = ["id", "username", "created_at"]

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.user.followers.filter(follower=request.user).exists()
        return False


class ProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Profile
        fields = ["display_name", "bio", "profile_picture", "password"]

    def validate_profile_picture(self, value):
        allowed_content_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }
        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in allowed_content_types:
            raise serializers.ValidationError("Only JPEG, PNG, and WEBP images are allowed.")

        try:
            image = Image.open(value)
            image.verify()
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError("Uploaded file is not a valid image.")
        finally:
            value.seek(0)

        return value

    def validate_password(self, value):
        validate_password(value, self.instance.user if self.instance else None)
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.user.set_password(password)
            instance.user.save()
        return super().update(instance, validated_data)


class UserSearchSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name", read_only=True)
    profile_picture = serializers.ImageField(source="profile.profile_picture", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "profile_picture"]
