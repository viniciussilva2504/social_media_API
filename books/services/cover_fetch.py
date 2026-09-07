import io
from urllib.parse import urlparse
from uuid import uuid4

import requests
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

from books.services.ssrf_guard import is_safe_host

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_COVER_SIZE = 5 * 1024 * 1024  # 5MB
FETCH_TIMEOUT = 5  # seconds


class CoverFetchError(Exception):
    """Raised when a cover image can't be safely fetched from a URL."""


def fetch_cover_from_url(url: str) -> ContentFile:
    """Download an image from `url` and return it as a validated ContentFile.

    Raises CoverFetchError (with a user-facing message) on any failure:
    invalid scheme, unsafe/internal host, redirect, oversized response,
    disallowed content type, or a payload that isn't a decodable image.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise CoverFetchError("Cover URL must be a valid http(s) link.")

    if not is_safe_host(parsed.hostname):
        raise CoverFetchError("That cover URL can't be fetched.")

    try:
        response = requests.get(
            url,
            stream=True,
            timeout=FETCH_TIMEOUT,
            allow_redirects=False,
            headers={"User-Agent": "ant.social-cover-fetch/1.0"},
        )
    except requests.RequestException:
        raise CoverFetchError("Could not download the image from that URL.")

    with response:
        if response.status_code != 200:
            raise CoverFetchError("Could not download the image from that URL.")

        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise CoverFetchError("Cover URL must point directly to a JPEG, PNG, or WebP image.")

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > MAX_COVER_SIZE:
                    raise CoverFetchError("Cover image must be under 5MB.")
            except ValueError:
                pass

        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            total += len(chunk)
            if total > MAX_COVER_SIZE:
                raise CoverFetchError("Cover image must be under 5MB.")
            chunks.append(chunk)
        data = b"".join(chunks)

    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise CoverFetchError("That URL doesn't point to a valid image.")

    extension = ALLOWED_CONTENT_TYPES[content_type]
    filename = f"{uuid4().hex}.{extension}"
    return ContentFile(data, name=filename)
