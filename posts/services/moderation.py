import logging
import os

import requests
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

PERSPECTIVE_API_KEY = os.environ.get("PERSPECTIVE_API_KEY", "")
PERSPECTIVE_THRESHOLD = float(os.environ.get("PERSPECTIVE_THRESHOLD", "0.7"))
PERSPECTIVE_URL = (
    "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
)


def check_toxicity(text: str) -> None:
    """Check text against Google Perspective API for toxicity.

    Raises ValidationError if the toxicity score exceeds the threshold.
    Silently skips when the API key is not configured or the API is
    unreachable, so the feature degrades gracefully.
    """
    if not PERSPECTIVE_API_KEY:
        return

    try:
        response = requests.post(
            PERSPECTIVE_URL,
            params={"key": PERSPECTIVE_API_KEY},
            json={
                "comment": {"text": text},
                "requestedAttributes": {"TOXICITY": {}},
                "languages": ["en", "pt"],
            },
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        score = (
            data.get("attributeScores", {})
            .get("TOXICITY", {})
            .get("summaryScore", {})
            .get("value", 0)
        )

        if score >= PERSPECTIVE_THRESHOLD:
            raise ValidationError(
                {
                    "detail": (
                        "Your content was flagged as potentially toxic. "
                        "Please revise it."
                    )
                }
            )
    except ValidationError:
        raise
    except requests.RequestException:
        logger.warning("Perspective API unavailable, skipping moderation check")
    except Exception:
        logger.exception("Unexpected error during moderation check")
