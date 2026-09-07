from unittest.mock import patch, MagicMock

from django.test import TestCase

from books.services.url_import import import_book_metadata, BookImportError


def _mock_response(status_code=200, content_type="text/html; charset=utf-8", html="", headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    hdrs = {"Content-Type": content_type}
    if headers:
        hdrs.update(headers)
    resp.headers = hdrs
    resp.encoding = "utf-8"
    resp.iter_content.return_value = [html.encode("utf-8")]
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    resp.close = MagicMock()
    return resp


OG_HTML = """
<html><head>
<title>Fallback Title — Some Store</title>
<meta property="og:title" content="Para acabar de vez com Eddy Bellegueule" />
<meta property="og:description" content="Um romance intenso sobre classe e violencia." />
<meta property="og:image" content="https://cdn.example.com/covers/eddy.jpg" />
</head><body><h1>page body, should never be parsed</h1></body></html>
"""

JSON_LD_HTML = """
<html><head>
<meta property="og:title" content="Some Book" />
<meta property="og:image" content="/covers/relative.jpg" />
<script type="application/ld+json">
{"@type": "Book", "name": "Some Book", "author": {"@type": "Person", "name": "Jane Author"},
 "description": "A book about things."}
</script>
</head><body></body></html>
"""


class ImportBookMetadataTest(TestCase):
    def test_rejects_unsafe_host(self):
        with self.assertRaises(BookImportError):
            import_book_metadata("http://127.0.0.1/some-book")

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(BookImportError):
            import_book_metadata("ftp://example.com/book")

    @patch("books.services.url_import.requests.get")
    def test_extracts_og_tags(self, mock_get):
        mock_get.return_value = _mock_response(html=OG_HTML)
        data = import_book_metadata("https://example.com/book/eddy")
        self.assertEqual(data["title"], "Para acabar de vez com Eddy Bellegueule")
        self.assertEqual(data["description"], "Um romance intenso sobre classe e violencia.")
        self.assertEqual(data["cover_image_url"], "https://cdn.example.com/covers/eddy.jpg")

    @patch("books.services.url_import.requests.get")
    def test_extracts_author_from_json_ld_and_resolves_relative_image(self, mock_get):
        mock_get.return_value = _mock_response(html=JSON_LD_HTML)
        data = import_book_metadata("https://example.com/book/some-book")
        self.assertEqual(data["title"], "Some Book")
        self.assertEqual(data["author"], "Jane Author")
        self.assertEqual(data["description"], "A book about things.")
        self.assertEqual(data["cover_image_url"], "https://example.com/covers/relative.jpg")

    @patch("books.services.url_import.requests.get")
    def test_drops_url_shaped_author_from_meta_tag(self, mock_get):
        html_doc = """
        <html><head>
        <meta property="og:title" content="A Book" />
        <meta property="book:author" content="https://example.com/authors/someone" />
        </head></html>
        """
        mock_get.return_value = _mock_response(html=html_doc)
        data = import_book_metadata("https://example.com/book/a-book")
        self.assertEqual(data["author"], "")

    @patch("books.services.url_import.requests.get")
    def test_raises_when_no_title_found(self, mock_get):
        mock_get.return_value = _mock_response(html="<html><head></head><body></body></html>")
        with self.assertRaises(BookImportError):
            import_book_metadata("https://example.com/blank")

    @patch("books.services.url_import.requests.get")
    def test_rejects_non_html_content_type(self, mock_get):
        mock_get.return_value = _mock_response(content_type="application/json", html="{}")
        with self.assertRaises(BookImportError):
            import_book_metadata("https://example.com/api/book")

    @patch("books.services.url_import.requests.get")
    def test_follows_safe_redirect(self, mock_get):
        redirect_resp = _mock_response(status_code=302, headers={"Location": "https://example.com/final"})
        final_resp = _mock_response(html=OG_HTML)
        mock_get.side_effect = [redirect_resp, final_resp]

        data = import_book_metadata("https://example.com/short-link")
        self.assertEqual(data["title"], "Para acabar de vez com Eddy Bellegueule")
        self.assertEqual(mock_get.call_count, 2)

    @patch("books.services.url_import.requests.get")
    def test_rejects_redirect_to_unsafe_host(self, mock_get):
        redirect_resp = _mock_response(status_code=302, headers={"Location": "http://169.254.169.254/latest"})
        mock_get.return_value = redirect_resp

        with self.assertRaises(BookImportError):
            import_book_metadata("https://example.com/short-link")

    @patch("books.services.url_import.requests.get")
    def test_raises_on_bot_check_interstitial(self, mock_get):
        # Amazon (and similar sites) return HTTP 200 but serve a "prove
        # you're not a robot" page instead of the product: the only
        # recognizable content is the bare site name in <title>, nothing
        # else. That should surface as a clear error, not fake data.
        html_doc = '<html><head><title>Amazon.com.br</title></head><body></body></html>'
        mock_get.return_value = _mock_response(html=html_doc)
        with self.assertRaises(BookImportError):
            import_book_metadata("https://www.amazon.com.br/dp/8582851995")

    @patch("books.services.url_import.requests.get")
    def test_allows_minimal_title_matching_unrelated_domain(self, mock_get):
        # A real page whose title just happens to equal a *different*
        # site's brand (not its own hostname) should still import fine.
        html_doc = '<html><head><title>Amazon.com.br</title></head><body></body></html>'
        mock_get.return_value = _mock_response(html=html_doc)
        data = import_book_metadata("https://example.com/book/some-book")
        self.assertEqual(data["title"], "Amazon.com.br")

    @patch("books.services.url_import.requests.get")
    def test_truncates_overly_long_title_and_description(self, mock_get):
        html_doc = (
            '<html><head><meta property="og:title" content="'
            + ("T" * 300)
            + '" /><meta property="og:description" content="'
            + ("D" * 900)
            + '" /></head></html>'
        )
        mock_get.return_value = _mock_response(html=html_doc)
        data = import_book_metadata("https://example.com/long")
        self.assertEqual(len(data["title"]), 200)
        self.assertEqual(len(data["description"]), 500)
