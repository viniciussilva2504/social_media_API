"""
Security & regression tests for known bugs.
Run: pytest tests/test_bugs.py -v
"""
import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from posts.models import Post, Comment
from accounts.models import Follow


class CommentOnInactivePostTest(TestCase):
    """BUG: API accepted comments on soft-deleted posts."""

    def setUp(self):
        self.client = APIClient()
        self.author = User.objects.create_user(username="author", password="pass1234!")
        self.commenter = User.objects.create_user(username="commenter", password="pass1234!")
        self.client.force_authenticate(user=self.commenter)
        self.post = Post.objects.create(author=self.author, content="Will be deleted")
        self.post.is_active = False
        self.post.save()

    def test_cannot_comment_on_inactive_post(self):
        """Commenting on a soft-deleted post must return 400, not 201."""
        resp = self.client.post(
            "/antisocial/v1/comment/",
            {"post": self.post.id, "content": "ghost comment"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 0)

    def test_can_comment_on_active_post(self):
        """Sanity check: commenting on active post still works."""
        self.post.is_active = True
        self.post.save()
        resp = self.client.post(
            "/antisocial/v1/comment/",
            {"post": self.post.id, "content": "valid comment"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class CommentInvalidPostIdTest(TestCase):
    """BUG: non-integer post_id in ?post_id= caused 500 ValueError."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pass1234!")
        self.client.force_authenticate(user=self.user)

    def test_invalid_post_id_returns_400_not_500(self):
        """?post_id=abc must return 400, not crash with 500."""
        resp = self.client.get("/antisocial/v1/comment/?post_id=abc")
        self.assertNotEqual(resp.status_code, 500)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_post_id_works(self):
        resp = self.client.get("/antisocial/v1/comment/?post_id=999")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ProfileMeUnauthenticatedTest(TestCase):
    """BUG: GET /profile/me/ without auth caused confusing 404 instead of 403."""

    def setUp(self):
        self.client = APIClient()

    def test_me_without_auth_returns_401_or_403(self):
        resp = self.client.get("/antisocial/v1/profile/me/")
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class LoginUsernameMaxLengthTest(TestCase):
    """BUG: LoginSerializer capped username at 80 chars; User model allows 150."""

    def setUp(self):
        self.client = APIClient()
        long_username = "a" * 120
        self.user = User.objects.create_user(username=long_username, password="longpass1234!")

    def test_login_with_long_username_succeeds(self):
        """User with username > 80 chars must be able to log in via API."""
        resp = self.client.post(
            "/antisocial/v1/login/",
            {"username": "a" * 120, "password": "longpass1234!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)


class SelfFollowAPITest(TestCase):
    """Verify self-follow is rejected at API level (DB constraint alone is not enough)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="selfuser", password="pass1234!")
        self.client.force_authenticate(user=self.user)

    def test_follow_self_returns_400(self):
        resp = self.client.post(f"/antisocial/v1/follow/toggle/{self.user.username}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("yourself", resp.data.get("detail", "").lower())


class PostContentMaxLengthTest(TestCase):
    """Post content over 280 chars must be rejected."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pass1234!")
        self.client.force_authenticate(user=self.user)

    def test_post_content_too_long(self):
        resp = self.client.post("/antisocial/v1/post/", {"content": "x" * 281})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class CommentContentMaxLengthTest(TestCase):
    """Comment content over 280 chars must be rejected."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pass1234!")
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(author=self.user, content="post")

    def test_comment_content_too_long(self):
        resp = self.client.post(
            "/antisocial/v1/comment/",
            {"post": self.post.id, "content": "x" * 281},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class PostOwnershipTest(TestCase):
    """Edit/delete must be refused for non-owners (IDOR check)."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username="owner", password="pass1234!")
        self.attacker = User.objects.create_user(username="attacker", password="pass1234!")
        self.post = Post.objects.create(author=self.owner, content="mine")

    def test_attacker_cannot_edit_post(self):
        self.client.force_authenticate(user=self.attacker)
        resp = self.client.patch(f"/antisocial/v1/post/{self.post.id}/", {"content": "hacked"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "mine")

    def test_attacker_cannot_delete_post(self):
        self.client.force_authenticate(user=self.attacker)
        resp = self.client.delete(f"/antisocial/v1/post/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_active)


class UnauthorizedFeedTest(TestCase):
    """Feed endpoint must require authentication."""

    def test_feed_requires_auth(self):
        client = APIClient()
        resp = client.get("/antisocial/v1/feed/")
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class DuplicateEmailRegistrationTest(TestCase):
    """Two accounts with the same email must be rejected."""

    def setUp(self):
        self.client = APIClient()
        User.objects.create_user(username="first", email="dup@example.com", password="pass1234!")

    def test_duplicate_email_rejected(self):
        resp = self.client.post("/antisocial/v1/register/", {
            "username": "second",
            "email": "dup@example.com",
            "password": "pass5678!A",
            "password_confirm": "pass5678!A",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LikeInactivePostTest(TestCase):
    """Liking a soft-deleted post must return 404."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pass1234!")
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(author=self.user, content="bye")
        self.post.is_active = False
        self.post.save()

    def test_like_inactive_post_is_404(self):
        resp = self.client.post(f"/antisocial/v1/like/toggle/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class RegisterEmptyUsernameTest(TestCase):
    """Empty username must be rejected."""

    def setUp(self):
        self.client = APIClient()

    def test_empty_username_rejected(self):
        resp = self.client.post("/antisocial/v1/register/", {
            "username": "",
            "password": "pass1234!",
            "password_confirm": "pass1234!",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
