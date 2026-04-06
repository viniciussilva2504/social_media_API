from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from posts.services.moderation import check_toxicity


class CheckToxicityNoKeyTest(TestCase):
    """When PERSPECTIVE_API_KEY is empty, moderation is skipped."""

    @patch("posts.services.moderation.PERSPECTIVE_API_KEY", "")
    def test_skips_when_no_key(self):
        # Should not raise — graceful degradation
        check_toxicity("some toxic garbage text")


class CheckToxicityWithKeyTest(TestCase):

    @patch("posts.services.moderation.PERSPECTIVE_API_KEY", "fake-key")
    @patch("posts.services.moderation.requests.post")
    def test_allows_clean_text(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "attributeScores": {
                "TOXICITY": {"summaryScore": {"value": 0.1}}
            }
        }
        mock_post.return_value = mock_resp
        # Should not raise
        check_toxicity("hello world, nice day!")
        mock_post.assert_called_once()

    @patch("posts.services.moderation.PERSPECTIVE_API_KEY", "fake-key")
    @patch("posts.services.moderation.PERSPECTIVE_THRESHOLD", 0.7)
    @patch("posts.services.moderation.requests.post")
    def test_rejects_toxic_text(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "attributeScores": {
                "TOXICITY": {"summaryScore": {"value": 0.95}}
            }
        }
        mock_post.return_value = mock_resp
        with self.assertRaises(ValidationError) as ctx:
            check_toxicity("extremely offensive content")
        self.assertIn("toxic", str(ctx.exception.detail))

    @patch("posts.services.moderation.PERSPECTIVE_API_KEY", "fake-key")
    @patch("posts.services.moderation.requests.post")
    def test_graceful_on_api_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.ConnectionError("timeout")
        # Should NOT raise — silently skip
        check_toxicity("some text")

    @patch("posts.services.moderation.PERSPECTIVE_API_KEY", "fake-key")
    @patch("posts.services.moderation.requests.post")
    def test_graceful_on_unexpected_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {}  # missing attributeScores
        mock_post.return_value = mock_resp
        # Should NOT raise — score defaults to 0
        check_toxicity("some text")
