from rest_framework import serializers
from django.contrib.auth.models import User

from accounts.models.profile import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
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
