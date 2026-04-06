from django.test import TestCase
from django.contrib.auth.models import User

from posts.models import Post


class FeedViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.login(username="testuser", password="testpass123!")

    def test_feed_view(self):
        resp = self.client.get("/feed/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "feed.html")

    def test_feed_requires_login(self):
        self.client.logout()
        resp = self.client.get("/feed/")
        self.assertEqual(resp.status_code, 302)

    def test_feed_pagination(self):
        for i in range(25):
            Post.objects.create(author=self.user, content=f"Post {i}")
        resp = self.client.get("/feed/")
        self.assertIn("posts", resp.context)
        self.assertEqual(resp.context["posts"].paginator.count, 25)

    def test_feed_page_2(self):
        for i in range(25):
            Post.objects.create(author=self.user, content=f"Post {i}")
        resp = self.client.get("/feed/?page=2")
        self.assertEqual(resp.status_code, 200)


class SearchViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.login(username="testuser", password="testpass123!")

    def test_search_empty(self):
        resp = self.client.get("/search/")
        self.assertEqual(resp.status_code, 200)

    def test_search_with_query(self):
        User.objects.create_user(username="findme", password="testpass123!")
        resp = self.client.get("/search/?q=findme")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "findme")

    def test_search_requires_login(self):
        self.client.logout()
        resp = self.client.get("/search/")
        self.assertEqual(resp.status_code, 302)


class CreatePostViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.login(username="testuser", password="testpass123!")

    def test_create_post_get(self):
        resp = self.client.get("/post/new/")
        self.assertEqual(resp.status_code, 200)

    def test_create_post_success(self):
        resp = self.client.post("/post/new/", {"content": "Hello world!"})
        self.assertRedirects(resp, "/feed/")
        self.assertTrue(Post.objects.filter(content="Hello world!").exists())

    def test_create_post_requires_login(self):
        self.client.logout()
        resp = self.client.post("/post/new/", {"content": "Hello"})
        self.assertEqual(resp.status_code, 302)


class PostDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.post = Post.objects.create(author=self.user, content="Test post")
        self.client.login(username="testuser", password="testpass123!")

    def test_post_detail(self):
        resp = self.client.get(f"/post/{self.post.pk}/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "post_detail.html")

    def test_post_detail_not_found(self):
        resp = self.client.get("/post/99999/")
        self.assertEqual(resp.status_code, 404)
