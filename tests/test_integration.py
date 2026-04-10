from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from posts.models import Post


class PermissionsTest(TestCase):
    """Tests for IsOwnerOrReadOnly and IsProfileOwner in real API usage."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="str0ngP@ss!")
        self.bob = User.objects.create_user("bob", password="str0ngP@ss!")
        self.client = APIClient()

    def test_anon_can_read_posts(self):
        Post.objects.create(author=self.alice, content="Public post")
        resp = self.client.get("/antisocial/v1/post/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_anon_cannot_create_post(self):
        resp = self.client.post("/antisocial/v1/post/", {"content": "Fail"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anon_can_read_profiles(self):
        resp = self.client.get("/antisocial/v1/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_owner_can_delete_own_post(self):
        self.client.force_authenticate(user=self.alice)
        post = Post.objects.create(author=self.alice, content="Mine")
        resp = self.client.delete(f"/antisocial/v1/post/{post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_owner_cannot_delete_post(self):
        self.client.force_authenticate(user=self.bob)
        post = Post.objects.create(author=self.alice, content="Not yours")
        resp = self.client.delete(f"/antisocial/v1/post/{post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_cannot_update_profile(self):
        self.client.force_authenticate(user=self.bob)
        resp = self.client.patch(
            "/antisocial/v1/profile/alice/", {"bio": "hacked"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class HealthcheckDegradedTest(TestCase):

    def test_healthcheck_ok(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "ok")
