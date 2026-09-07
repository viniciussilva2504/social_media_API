import io
from unittest.mock import patch, MagicMock

from django.test import TestCase
from PIL import Image

from books.services.cover_fetch import fetch_cover_from_url, CoverFetchError
from books.services.ssrf_guard import is_safe_host


def _fake_image_bytes(fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format=fmt)
    return buf.getvalue()


def _mock_response(status_code=200, content_type="image/png", data=b"", headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    hdrs = {"Content-Type": content_type}
    if headers:
        hdrs.update(headers)
    resp.headers = hdrs
    resp.iter_content.return_value = [data]
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


class SafeHostTest(TestCase):
    def test_rejects_loopback(self):
        self.assertFalse(is_safe_host("127.0.0.1"))
        self.assertFalse(is_safe_host("localhost"))

    def test_rejects_link_local_metadata_ip(self):
        self.assertFalse(is_safe_host("169.254.169.254"))

    def test_rejects_private_network(self):
        self.assertFalse(is_safe_host("10.0.0.5"))
        self.assertFalse(is_safe_host("192.168.1.1"))

    def test_rejects_unresolvable_host(self):
        self.assertFalse(is_safe_host("this-host-should-not-exist.invalid"))

    def test_accepts_public_ip(self):
        self.assertTrue(is_safe_host("8.8.8.8"))


class FetchCoverFromUrlTest(TestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("ftp://example.com/cover.jpg")

    def test_rejects_unsafe_host(self):
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("http://127.0.0.1/cover.jpg")

    def test_rejects_internal_metadata_host(self):
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("http://169.254.169.254/latest/meta-data/")

    @patch("books.services.cover_fetch.requests.get")
    def test_fetches_valid_image(self, mock_get):
        data = _fake_image_bytes("PNG")
        mock_get.return_value = _mock_response(200, "image/png", data)

        result = fetch_cover_from_url("https://example.com/cover.png")
        self.assertTrue(result.name.endswith(".png"))
        self.assertEqual(result.read(), data)

    @patch("books.services.cover_fetch.requests.get")
    def test_rejects_disallowed_content_type(self, mock_get):
        mock_get.return_value = _mock_response(200, "text/html", b"<html></html>")
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("https://example.com/not-an-image")

    @patch("books.services.cover_fetch.requests.get")
    def test_rejects_oversized_image(self, mock_get):
        mock_get.return_value = _mock_response(
            200, "image/png", b"", headers={"Content-Length": str(6 * 1024 * 1024)}
        )
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("https://example.com/huge.png")

    @patch("books.services.cover_fetch.requests.get")
    def test_rejects_non_image_payload_despite_header(self, mock_get):
        mock_get.return_value = _mock_response(200, "image/png", b"not actually an image")
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("https://example.com/fake.png")

    @patch("books.services.cover_fetch.requests.get")
    def test_rejects_redirect_response(self, mock_get):
        mock_get.return_value = _mock_response(302, "image/png", b"")
        with self.assertRaises(CoverFetchError):
            fetch_cover_from_url("https://example.com/redirecting.png")
