from django.test import TestCase
from django.contrib.auth.models import User

from posts.models import Post, Comment, Like


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.post = Post.objects.create(author=self.user, content="Test post")

    def test_post_creation(self):
        self.assertEqual(self.post.content, "Test post")
        self.assertTrue(self.post.is_active)

    def test_post_str(self):
        self.assertIn("@testuser", str(self.post))

    def test_likes_count_property(self):
        self.assertEqual(self.post.likes_count, 0)
        Like.objects.create(user=self.user, post=self.post)
        self.assertEqual(self.post.likes_count, 1)

    def test_comments_count_property(self):
        self.assertEqual(self.post.comments_count, 0)
        Comment.objects.create(author=self.user, post=self.post, content="Comment")
        self.assertEqual(self.post.comments_count, 1)

    def test_soft_delete(self):
        self.post.is_active = False
        self.post.save()
        self.assertFalse(
            Post.objects.filter(id=self.post.id, is_active=True).exists()
        )


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.post = Post.objects.create(author=self.user, content="Test post")

    def test_comment_creation(self):
        comment = Comment.objects.create(
            author=self.user, post=self.post, content="Nice post!"
        )
        self.assertIn("@testuser", str(comment))


class LikeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.post = Post.objects.create(author=self.user, content="Test post")

    def test_like_creation(self):
        like = Like.objects.create(user=self.user, post=self.post)
        self.assertIn("testuser", str(like))

    def test_unique_like(self):
        Like.objects.create(user=self.user, post=self.post)
        with self.assertRaises(Exception):
            Like.objects.create(user=self.user, post=self.post)
