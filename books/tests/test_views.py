import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from PIL import Image

from books.models import Book, BookComment
from books.services.cover_fetch import CoverFetchError
from books.services.url_import import BookImportError


class BookDetailCommentViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="testpass123!"
        )
        self.friend = User.objects.create_user(
            username="friend", password="testpass123!"
        )
        self.book = Book.objects.create(
            owner=self.owner, title="Some Book", book_author="Some Author"
        )

    def test_friend_can_comment_on_book(self):
        self.client.login(username="friend", password="testpass123!")
        resp = self.client.post(
            f"/book/{self.book.id}/",
            {"form_type": "comment", "content": "adding this to my wishlist"},
        )
        self.assertRedirects(resp, f"/book/{self.book.id}/")
        self.assertEqual(BookComment.objects.count(), 1)
        comment = BookComment.objects.first()
        self.assertEqual(comment.author, self.friend)
        self.assertEqual(comment.book, self.book)

    def test_owner_can_comment_on_own_book(self):
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.post(
            f"/book/{self.book.id}/",
            {"form_type": "comment", "content": "bumping this up"},
        )
        self.assertRedirects(resp, f"/book/{self.book.id}/")
        self.assertEqual(BookComment.objects.count(), 1)

    def test_anonymous_cannot_comment(self):
        resp = self.client.post(
            f"/book/{self.book.id}/",
            {"form_type": "comment", "content": "should not be saved"},
        )
        self.assertEqual(BookComment.objects.count(), 0)

    def test_empty_comment_is_rejected(self):
        self.client.login(username="friend", password="testpass123!")
        resp = self.client.post(
            f"/book/{self.book.id}/",
            {"form_type": "comment", "content": "   "},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(BookComment.objects.count(), 0)

    def test_comments_listed_on_book_detail_page(self):
        BookComment.objects.create(author=self.friend, book=self.book, content="great find")
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.get(f"/book/{self.book.id}/")
        self.assertContains(resp, "great find")

    def test_trade_request_still_works_alongside_comments(self):
        self.client.login(username="friend", password="testpass123!")
        resp = self.client.post(
            f"/book/{self.book.id}/",
            {
                "form_type": "trade_request",
                "offered_book": "Something else",
                "message": "wanna trade?",
            },
        )
        self.assertRedirects(resp, f"/book/{self.book.id}/")
        self.assertEqual(self.book.trade_requests.count(), 1)


def _valid_cover_file():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile("cover.jpg", buf.read(), content_type="image/jpeg")


class ToggleBookAvailabilityViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123!")
        self.other = User.objects.create_user(username="other", password="testpass123!")
        self.book = Book.objects.create(
            owner=self.owner, title="Some Book", book_author="Some Author"
        )

    def test_owner_can_mark_unavailable_then_available_again(self):
        self.client.login(username="owner", password="testpass123!")
        url = f"/book/{self.book.id}/toggle-availability/"

        self.client.post(url)
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_available)

        self.client.post(url)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_available)

    def test_non_owner_cannot_toggle(self):
        self.client.login(username="other", password="testpass123!")
        resp = self.client.post(f"/book/{self.book.id}/toggle-availability/")
        self.assertEqual(resp.status_code, 404)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_available)

    def test_anonymous_cannot_toggle(self):
        resp = self.client.post(f"/book/{self.book.id}/toggle-availability/")
        self.assertNotEqual(resp.status_code, 200)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_available)

    def test_get_not_allowed(self):
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.get(f"/book/{self.book.id}/toggle-availability/")
        self.assertEqual(resp.status_code, 405)


class AddBookViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="testpass123!")
        self.client.login(username="owner", password="testpass123!")

    def test_cover_is_required_file_or_url(self):
        resp = self.client.post(
            "/biblioteca/owner/add/",
            {"title": "A Book", "book_author": "An Author", "description": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)
        # the user shouldn't have to retype what they already entered
        self.assertContains(resp, 'value="A Book"')
        self.assertContains(resp, 'value="An Author"')

    def test_description_over_500_chars_preserves_typed_fields(self):
        resp = self.client.post(
            "/biblioteca/owner/add/",
            {
                "title": "A Book",
                "book_author": "An Author",
                "description": "x" * 501,
                "cover": _valid_cover_file(),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)
        self.assertContains(resp, 'value="A Book"')
        self.assertContains(resp, 'value="An Author"')

    def test_create_book_with_uploaded_cover(self):
        resp = self.client.post(
            "/biblioteca/owner/add/",
            {
                "title": "A Book",
                "book_author": "An Author",
                "description": "",
                "cover": _valid_cover_file(),
            },
        )
        self.assertRedirects(resp, "/biblioteca/owner/")
        self.assertEqual(Book.objects.count(), 1)
        self.assertTrue(Book.objects.first().cover)

    @patch("books.views.fetch_cover_from_url")
    def test_create_book_with_cover_url(self, mock_fetch):
        from django.core.files.base import ContentFile
        mock_fetch.return_value = ContentFile(b"fake-image-bytes", name="cover.jpg")

        resp = self.client.post(
            "/biblioteca/owner/add/",
            {
                "title": "A Book",
                "book_author": "An Author",
                "description": "",
                "cover_url": "https://example.com/cover.jpg",
            },
        )
        self.assertRedirects(resp, "/biblioteca/owner/")
        mock_fetch.assert_called_once_with("https://example.com/cover.jpg")
        self.assertEqual(Book.objects.count(), 1)
        self.assertTrue(Book.objects.first().cover)

    @patch("books.views.fetch_cover_from_url")
    def test_invalid_cover_url_shows_error_and_preserves_fields(self, mock_fetch):
        mock_fetch.side_effect = CoverFetchError("That cover URL can't be fetched.")

        resp = self.client.post(
            "/biblioteca/owner/add/",
            {
                "title": "A Book",
                "book_author": "An Author",
                "description": "",
                "cover_url": "http://127.0.0.1/cover.jpg",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)
        self.assertContains(resp, "That cover URL can&#x27;t be fetched.")
        self.assertContains(resp, 'value="A Book"')


class ImportBookPreviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="testpass123!")

    def test_requires_login(self):
        resp = self.client.post(
            "/book-import-preview/",
            data='{"url": "https://example.com/book"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 302)  # redirected to login

    def test_requires_get_not_allowed(self):
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.get("/book-import-preview/")
        self.assertEqual(resp.status_code, 405)

    def test_missing_url_returns_400(self):
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.post(
            "/book-import-preview/", data="{}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])

    def test_invalid_json_body_returns_400(self):
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.post(
            "/book-import-preview/", data="not json", content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    @patch("books.views.import_book_metadata")
    def test_successful_import_returns_metadata(self, mock_import):
        mock_import.return_value = {
            "title": "A Book",
            "author": "An Author",
            "description": "A description.",
            "cover_image_url": "https://cdn.example.com/cover.jpg",
        }
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.post(
            "/book-import-preview/",
            data='{"url": "https://example.com/book"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["title"], "A Book")
        self.assertEqual(data["cover_image_url"], "https://cdn.example.com/cover.jpg")
        mock_import.assert_called_once_with("https://example.com/book")

    @patch("books.views.import_book_metadata")
    def test_import_error_returns_400_with_message(self, mock_import):
        mock_import.side_effect = BookImportError("That link can't be fetched.")
        self.client.login(username="owner", password="testpass123!")
        resp = self.client.post(
            "/book-import-preview/",
            data='{"url": "http://127.0.0.1/book"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "That link can't be fetched.")
