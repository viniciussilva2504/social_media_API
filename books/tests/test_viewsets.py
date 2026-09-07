from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

from books.models import Book, BookComment


class BookViewSetAvailabilityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username="owner", password="testpass123!")
        self.other = User.objects.create_user(username="other", password="testpass123!")
        self.book = Book.objects.create(
            owner=self.owner, title="Some Book", book_author="Some Author", is_available=False
        )

    def test_unavailable_book_excluded_from_list(self):
        resp = self.client.get("/antisocial/v1/book/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [b["id"] for b in resp.data["results"]]
        self.assertNotIn(self.book.id, ids)

    def test_owner_can_still_retrieve_unavailable_book(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(f"/antisocial/v1/book/{self.book.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_owner_can_toggle_unavailable_book_back_via_api(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.patch(
            f"/antisocial/v1/book/{self.book.id}/", {"is_available": True}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_available)


class BookCommentViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(
            owner=self.other, title="Some Book", book_author="Some Author"
        )

    def test_create_comment(self):
        resp = self.client.post(
            "/antisocial/v1/book-comment/",
            {"book": self.book.id, "content": "Nice pick!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_username"], "testuser")
        self.assertEqual(resp.data["content"], "Nice pick!")

    def test_owner_can_also_comment(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.post(
            "/antisocial/v1/book-comment/",
            {"book": self.book.id, "content": "Replying on my own book"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_comment_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post(
            "/antisocial/v1/book-comment/",
            {"book": self.book.id, "content": "Fail"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_comments_by_book(self):
        BookComment.objects.create(author=self.user, book=self.book, content="C1")
        other_book = Book.objects.create(
            owner=self.other, title="Another Book", book_author="Another Author"
        )
        BookComment.objects.create(author=self.user, book=other_book, content="C2")

        resp = self.client.get(f"/antisocial/v1/book-comment/?book_id={self.book.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["content"], "C1")

    def test_cannot_delete_other_users_comment(self):
        comment = BookComment.objects.create(
            author=self.other, book=self.book, content="Other's comment"
        )
        resp = self.client.delete(f"/antisocial/v1/book-comment/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_comment_rejects_content_longer_than_280(self):
        resp = self.client.post(
            "/antisocial/v1/book-comment/",
            {"book": self.book.id, "content": "x" * 281},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", resp.data)
