from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

from posts.models import Post, Comment, Like
from accounts.models import Follow


class PostViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(author=self.user, content="My post")

    def test_list_posts(self):
        resp = self.client.get("/antisocial/v1/post/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_post(self):
        resp = self.client.post("/antisocial/v1/post/", {"content": "New post"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_username"], "testuser")

    def test_create_post_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post("/antisocial/v1/post/", {"content": "Fail"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_post(self):
        resp = self.client.patch(
            f"/antisocial/v1/post/{self.post.id}/", {"content": "Edited"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "Edited")

    def test_cannot_update_other_post(self):
        other_post = Post.objects.create(author=self.other, content="Other post")
        resp = self.client.patch(
            f"/antisocial/v1/post/{other_post.id}/", {"content": "Hacked"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_post(self):
        resp = self.client.delete(f"/antisocial/v1/post/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_active)

    def test_soft_deleted_post_not_in_list(self):
        self.post.is_active = False
        self.post.save()
        resp = self.client.get("/antisocial/v1/post/")
        post_ids = [p["id"] for p in resp.data["results"]]
        self.assertNotIn(self.post.id, post_ids)

    def test_post_includes_counts(self):
        Like.objects.create(user=self.user, post=self.post)
        Comment.objects.create(author=self.user, post=self.post, content="Yep")
        resp = self.client.get(f"/antisocial/v1/post/{self.post.id}/")
        self.assertEqual(resp.data["likes_count"], 1)
        self.assertEqual(resp.data["comments_count"], 1)
        self.assertTrue(resp.data["is_liked"])


class FeedViewSetTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="testpass123!"
        )
        self.stranger = User.objects.create_user(
            username="stranger", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, following=self.other)

    def test_feed_shows_all_active_posts(self):
        Post.objects.create(author=self.user, content="My post")
        Post.objects.create(author=self.other, content="Followed post")
        Post.objects.create(author=self.stranger, content="Stranger post")
        resp = self.client.get("/antisocial/v1/feed/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        contents = [p["content"] for p in resp.data["results"]]
        self.assertIn("My post", contents)
        self.assertIn("Followed post", contents)
        self.assertIn("Stranger post", contents)

    def test_feed_excludes_soft_deleted(self):
        post = Post.objects.create(author=self.other, content="Deleted")
        post.is_active = False
        post.save()
        resp = self.client.get("/antisocial/v1/feed/")
        contents = [p["content"] for p in resp.data["results"]]
        self.assertNotIn("Deleted", contents)

    def test_feed_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/antisocial/v1/feed/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class CommentViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(author=self.user, content="Post")

    def test_create_comment(self):
        resp = self.client.post(
            "/antisocial/v1/comment/",
            {"post": self.post.id, "content": "Nice!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_username"], "testuser")

    def test_list_comments_by_post(self):
        Comment.objects.create(author=self.user, post=self.post, content="C1")
        resp = self.client.get(f"/antisocial/v1/comment/?post_id={self.post.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_cannot_delete_other_comment(self):
        comment = Comment.objects.create(
            author=self.other, post=self.post, content="Other"
        )
        resp = self.client.delete(f"/antisocial/v1/comment/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class LikeViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(author=self.user, content="Post")

    def test_like_toggle_on(self):
        resp = self.client.post(f"/antisocial/v1/like/toggle/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "liked")
        self.assertEqual(resp.data["likes_count"], 1)

    def test_like_toggle_off(self):
        Like.objects.create(user=self.user, post=self.post)
        resp = self.client.post(f"/antisocial/v1/like/toggle/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "unliked")
        self.assertEqual(resp.data["likes_count"], 0)

    def test_like_soft_deleted_post_fails(self):
        self.post.is_active = False
        self.post.save()
        resp = self.client.post(f"/antisocial/v1/like/toggle/{self.post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
