import html
import json
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

from books.services.ssrf_guard import is_safe_host

FETCH_TIMEOUT = 5  # seconds
MAX_HTML_SIZE = 3 * 1024 * 1024  # 3MB
MAX_REDIRECTS = 3
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 500

# Identify honestly, like a chat app's link-preview bot would — this reads
# only public <head> preview metadata, the same data a WhatsApp/Slack link
# card uses. Some sites (notably Amazon) block this outright; that's a
# known, accepted limitation rather than something we try to evade.
USER_AGENT = "ant.social-link-preview/1.0 (+book import)"


class BookImportError(Exception):
    """Raised when book metadata can't be safely imported from a URL."""


class _HeadMetaParser(HTMLParser):
    """Pulls <meta>, <title>, and JSON-LD <script> blocks out of <head>.

    Stops consuming once </head> closes, so a multi-megabyte page body
    never gets parsed just to read a handful of preview tags.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title = ""
        self.json_ld_blocks = []
        self._in_title = False
        self._in_json_ld = False
        self._json_ld_buffer = []
        self.head_closed = False

    def handle_starttag(self, tag, attrs):
        if self.head_closed:
            return
        attrs_dict = {k: v for k, v in attrs if v is not None}
        if tag == "meta":
            key = attrs_dict.get("property") or attrs_dict.get("name")
            content = attrs_dict.get("content")
            if key and content is not None:
                self.meta.setdefault(key.lower(), content)
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and attrs_dict.get("type") == "application/ld+json":
            self._in_json_ld = True
            self._json_ld_buffer = []

    def handle_endtag(self, tag):
        if self.head_closed:
            return
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_json_ld:
            self._in_json_ld = False
            self.json_ld_blocks.append("".join(self._json_ld_buffer))
        elif tag == "head":
            self.head_closed = True

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_json_ld:
            self._json_ld_buffer.append(data)


def _looks_like_a_blocked_page(title, description, author, image, hostname):
    """Detect a bot-check / interstitial page dressed up as a real response.

    Some retailers (notably Amazon) return HTTP 200 for automated requests
    but serve a "prove you're not a robot" page instead of the product —
    its only recognizable content is a bare site name in <title>, with no
    other preview metadata at all. That combination (title *is* the site's
    own domain/brand, and nothing else was extracted) is specific enough
    that a genuine, minimal book page essentially never matches it.
    """
    if description or author or image:
        return False

    hostname = (hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    candidates = {hostname, hostname.split(".")[0]} if hostname else set()

    return title.strip().lower() in candidates


def _extract_json_ld_book(blocks):
    """Look for a schema.org Book/Product entry — the most reliable source
    of a structured author name (Open Graph has no plain "author" field)."""
    candidates = []
    for block in blocks:
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, TypeError):
            continue
        candidates.extend(data if isinstance(data, list) else [data])

    for item in candidates:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("@graph"), list):
            candidates.extend(item["@graph"])
            continue

        item_type = item.get("@type", "")
        types = item_type if isinstance(item_type, list) else [item_type]
        if not any(t in ("Book", "Product") for t in types):
            continue

        author = item.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        elif isinstance(author, list) and author:
            first = author[0]
            author = first.get("name") if isinstance(first, dict) else str(first)

        return {
            "title": item.get("name"),
            "author": author if isinstance(author, str) else None,
            "description": item.get("description"),
            "image": item.get("image"),
        }
    return {}


def _fetch_html(url):
    """GET a page's HTML, re-validating the host on every redirect hop —
    a redirect Location is never trusted blindly (SSRF guard)."""
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise BookImportError("That doesn't look like a valid link.")
        if not is_safe_host(parsed.hostname):
            raise BookImportError("That link can't be fetched.")

        try:
            response = requests.get(
                current_url,
                stream=True,
                timeout=FETCH_TIMEOUT,
                allow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.RequestException:
            raise BookImportError("Could not reach that link.")

        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise BookImportError("Could not reach that link.")
            current_url = urljoin(current_url, location)
            continue

        with response:
            if response.status_code != 200:
                raise BookImportError(
                    "Could not fetch that page (it may be blocking automated requests)."
                )

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                raise BookImportError("That link doesn't point to a web page.")

            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                total += len(chunk)
                if total > MAX_HTML_SIZE:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)

        return raw.decode(response.encoding or "utf-8", errors="ignore"), current_url

    raise BookImportError("Too many redirects.")


def import_book_metadata(url: str) -> dict:
    """Best-effort extraction of title/author/description/cover from a
    book or product page — via its Open Graph tags and any schema.org
    Book/Product JSON-LD, the same public preview metadata a chat app
    reads to render a link card.

    This is intentionally generic (works across bookstores, not just one
    retailer) and only ever reads <head>. Some sites actively block
    automated requests and will fail to import — that's surfaced as a
    BookImportError so the caller can fall back to manual entry.
    """
    html_text, final_url = _fetch_html(url)

    parser = _HeadMetaParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass  # best-effort: malformed HTML shouldn't break the import

    meta = parser.meta
    json_ld = _extract_json_ld_book(parser.json_ld_blocks)

    title = meta.get("og:title") or json_ld.get("title") or html.unescape(parser.title).strip()
    description = (
        meta.get("og:description") or meta.get("description") or json_ld.get("description") or ""
    )
    # og:"book:author"/"author" are frequently a profile *URL* per the Open
    # Graph book-type spec, not a plain name — JSON-LD's author.name is far
    # more reliable, so it takes priority; a URL-shaped fallback is dropped.
    author = json_ld.get("author") or meta.get("book:author") or meta.get("author") or ""
    if author.startswith(("http://", "https://")):
        author = ""

    image = meta.get("og:image") or meta.get("twitter:image") or json_ld.get("image")
    if isinstance(image, list) and image:
        image = image[0]
    if isinstance(image, str) and image.strip():
        image = urljoin(final_url, image.strip())
    else:
        image = None

    title = html.unescape(title).strip()
    if not title:
        raise BookImportError("Could not find a book title on that page.")

    description = html.unescape(description).strip()
    author = html.unescape(author).strip()
    hostname = urlparse(final_url).hostname
    if _looks_like_a_blocked_page(title, description, author, image, hostname):
        raise BookImportError(
            "That site blocked the import request. Please fill in the details manually."
        )

    return {
        "title": title[:MAX_TITLE_LENGTH],
        "author": author[:MAX_TITLE_LENGTH],
        "description": description[:MAX_DESCRIPTION_LENGTH],
        "cover_image_url": image,
    }
