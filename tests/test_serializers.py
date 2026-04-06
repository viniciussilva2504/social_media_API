from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from io import BytesIO
from PIL import Image

from accounts.models import Follow
from accounts.serializers.auth_serializer import RegisterSerializer, LoginSerializer
from accounts.serializers.follow_serializer import FollowSerializer
from accounts.serializers.profile_serializer import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    UserSearchSerializer,
)
from posts.models import Post, Comment, Like
from posts.serializers.post_serializer import PostSerializer
from posts.serializers.comment_serializer import CommentSerializer
from posts.serializers.like_serializer import LikeSerializer


def _make_image(fmt="PNG", size=(10, 10)):
    buf = BytesIO()
    Image.new("RGB", size, "red").save(buf, format=fmt)
    buf.seek(0)
    return buf


# ── accounts ─────────────────────────────────────────────


class RegisterSerializerTest(TestCase):

    def test_valid_registration(self):
        data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "str0ngP@ss!",
            "password_confirm": "str0ngP@ss!",
        }
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.username, "alice")
        self.assertTrue(user.check_password("str0ngP@ss!"))

    def test_password_mismatch(self):
        data = {
            "username": "bob",
            "password": "str0ngP@ss!",
            "password_confirm": "different1!",
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("password_confirm", s.errors)

    def test_weak_password_rejected(self):
        data = {
            "username": "weak",
            "password": "12345678",
            "password_confirm": "12345678",
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_duplicate_email_rejected(self):
        User.objects.create_user("existing", email="taken@e.com", password="P@ssw0rd!")
        data = {
            "username": "new",
            "email": "taken@e.com",
            "password": "str0ngP@ss!",
            "password_confirm": "str0ngP@ss!",
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_blank_username_rejected(self):
        data = {
            "username": "",
            "password": "str0ngP@ss!",
            "password_confirm": "str0ngP@ss!",
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("username", s.errors)

    def test_password_not_in_output(self):
        data = {
            "username": "secret",
            "password": "str0ngP@ss!",
            "password_confirm": "str0ngP@ss!",
        }
        s = RegisterSerializer(data=data)
        s.is_valid(raise_exception=True)
        s.save()
        self.assertNotIn("password", s.data)
        self.assertNotIn("password_confirm", s.data)


class LoginSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("loginuser", password="str0ngP@ss!")

    def test_valid_credentials(self):
        s = LoginSerializer(data={"username": "loginuser", "password": "str0ngP@ss!"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["user"], self.user)

    def test_bad_password(self):
        s = LoginSerializer(data={"username": "loginuser", "password": "wrong"})
        self.assertFalse(s.is_valid())

    def test_nonexistent_user(self):
        s = LoginSerializer(data={"username": "ghost", "password": "whatever"})
        self.assertFalse(s.is_valid())


class FollowSerializerTest(TestCase):

    def setUp(self):
        self.u1 = User.objects.create_user("u1", password="str0ngP@ss!")
        self.u2 = User.objects.create_user("u2", password="str0ngP@ss!")
        self.follow = Follow.objects.create(follower=self.u1, following=self.u2)

    def test_serialized_fields(self):
        s = FollowSerializer(self.follow)
        self.assertEqual(s.data["follower_username"], "u1")
        self.assertEqual(s.data["following_username"], "u2")
        self.assertIn("created_at", s.data)

    def test_read_only_fields(self):
        s = FollowSerializer(self.follow, data={"follower_username": "hacked"}, partial=True)
        s.is_valid()
        # follower_username is read_only — should not change
        self.assertEqual(s.validated_data.get("follower_username"), None)


class ProfileSerializerTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user("profuser", password="str0ngP@ss!")
        self.other = User.objects.create_user("other", password="str0ngP@ss!")
        self.profile = self.user.profile

    def test_output_fields(self):
        request = self.factory.get("/")
        request.user = self.other
        s = ProfileSerializer(self.profile, context={"request": request})
        data = s.data
        self.assertEqual(data["username"], "profuser")
        self.assertIn("display_name", data)
        self.assertIn("bio", data)
        self.assertIn("is_following", data)
        self.assertFalse(data["is_following"])

    def test_is_following_true(self):
        Follow.objects.create(follower=self.other, following=self.user)
        request = self.factory.get("/")
        request.user = self.other
        s = ProfileSerializer(self.profile, context={"request": request})
        self.assertTrue(s.data["is_following"])

    def test_is_following_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        s = ProfileSerializer(self.profile, context={"request": request})
        self.assertFalse(s.data["is_following"])

    def test_username_is_read_only(self):
        s = ProfileSerializer(self.profile, data={"username": "hacked"}, partial=True)
        s.is_valid()
        self.assertNotIn("username", s.validated_data)


class ProfileUpdateSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("upd", password="str0ngP@ss!")
        self.profile = self.user.profile

    def test_update_display_name(self):
        s = ProfileUpdateSerializer(self.profile, data={"display_name": "New Name"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.display_name, "New Name")

    def test_password_change(self):
        s = ProfileUpdateSerializer(
            self.profile, data={"password": "N3wStr0ng!"}, partial=True
        )
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("N3wStr0ng!"))

    def test_weak_password_rejected(self):
        s = ProfileUpdateSerializer(
            self.profile, data={"password": "1234"}, partial=True
        )
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_invalid_image_rejected(self):
        fake = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")
        s = ProfileUpdateSerializer(
            self.profile, data={"profile_picture": fake}, partial=True
        )
        self.assertFalse(s.is_valid())
        self.assertIn("profile_picture", s.errors)

    def test_valid_image_accepted(self):
        buf = _make_image()
        img = SimpleUploadedFile("pic.png", buf.read(), content_type="image/png")
        s = ProfileUpdateSerializer(
            self.profile, data={"profile_picture": img}, partial=True
        )
        self.assertTrue(s.is_valid(), s.errors)


class UserSearchSerializerTest(TestCase):

    def test_output_fields(self):
        user = User.objects.create_user("searchme", password="str0ngP@ss!")
        user.profile.display_name = "Search Me"
        user.profile.save()
        s = UserSearchSerializer(user)
        self.assertEqual(s.data["username"], "searchme")
        self.assertEqual(s.data["display_name"], "Search Me")
        self.assertIn("profile_picture", s.data)


# ── posts ────────────────────────────────────────────────


class PostSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("author", password="str0ngP@ss!")
        self.post = Post.objects.create(author=self.user, content="Hello world")

    def test_read_only_fields(self):
        s = PostSerializer(data={"content": "new", "author_username": "hacked"})
        s.is_valid()
        self.assertNotIn("author_username", s.validated_data)

    def test_output_includes_author_info(self):
        from django.db.models import Count, Value
        from django.db.models.functions import Coalesce
        qs = Post.objects.filter(pk=self.post.pk).annotate(
            _likes_count=Count("likes", distinct=True),
            _comments_count=Count("comments", distinct=True),
        )
        post = qs.first()
        post._is_liked = False
        s = PostSerializer(post)
        self.assertEqual(s.data["author_username"], "author")
        self.assertEqual(s.data["author_display_name"], "author")
        self.assertEqual(s.data["likes_count"], 0)
        self.assertEqual(s.data["comments_count"], 0)
        self.assertFalse(s.data["is_liked"])

    def test_content_required(self):
        s = PostSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("content", s.errors)

    def test_content_max_length(self):
        s = PostSerializer(data={"content": "x" * 281})
        self.assertFalse(s.is_valid())
        self.assertIn("content", s.errors)


class CommentSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("commenter", password="str0ngP@ss!")
        self.post = Post.objects.create(author=self.user, content="Post")

    def test_valid_comment(self):
        s = CommentSerializer(data={"post": self.post.id, "content": "Nice!"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_post_required(self):
        s = CommentSerializer(data={"content": "Orphan comment"})
        self.assertFalse(s.is_valid())
        self.assertIn("post", s.errors)

    def test_content_required(self):
        s = CommentSerializer(data={"post": self.post.id})
        self.assertFalse(s.is_valid())
        self.assertIn("content", s.errors)

    def test_content_max_length(self):
        s = CommentSerializer(data={"post": self.post.id, "content": "x" * 281})
        self.assertFalse(s.is_valid())
        self.assertIn("content", s.errors)

    def test_read_only_author_fields(self):
        comment = Comment.objects.create(author=self.user, post=self.post, content="Hi")
        s = CommentSerializer(comment)
        self.assertEqual(s.data["author_username"], "commenter")
        self.assertEqual(s.data["author_display_name"], "commenter")


class LikeSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("liker", password="str0ngP@ss!")
        self.post = Post.objects.create(author=self.user, content="Likeable")
        self.like = Like.objects.create(user=self.user, post=self.post)

    def test_output_fields(self):
        s = LikeSerializer(self.like)
        self.assertEqual(s.data["username"], "liker")
        self.assertEqual(s.data["post"], self.post.id)
        self.assertIn("created_at", s.data)

    def test_username_read_only(self):
        s = LikeSerializer(data={"username": "fake", "post": self.post.id})
        s.is_valid()
        self.assertNotIn("username", s.validated_data)
