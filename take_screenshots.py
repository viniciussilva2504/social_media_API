"""
Script para tirar screenshots do ant.social para o README.
Requer: pip install playwright && playwright install chromium

Uso:
  python take_screenshots.py
  python take_screenshots.py --username admin --password admin123
"""

import argparse
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
IMG_DIR = Path(__file__).parent / "IMG"


def take_screenshots(username: str, password: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Instala o playwright: pip install playwright && playwright install chromium")
        sys.exit(1)

    IMG_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # 1. Home
        print("→ home.png")
        page.goto(BASE_URL)
        page.wait_for_timeout(800)
        page.screenshot(path=IMG_DIR / "home.png", full_page=False)

        # 2. Register
        print("→ register.png")
        page.goto(f"{BASE_URL}/register/")
        page.wait_for_timeout(500)
        page.screenshot(path=IMG_DIR / "register.png", full_page=False)

        # 3. API docs (Swagger)
        print("→ api-docs.png")
        page.goto(f"{BASE_URL}/api/docs/")
        page.wait_for_timeout(1500)
        page.screenshot(path=IMG_DIR / "api-docs.png", full_page=False)

        # Login
        print(f"→ A fazer login como '{username}'...")
        page.goto(f"{BASE_URL}/login/")
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("button[type=submit], input[type=submit]")
        page.wait_for_url(f"{BASE_URL}/feed/", timeout=5000)
        print("  Login OK")

        # 4. Feed
        print("→ feed.png")
        page.wait_for_timeout(600)
        page.screenshot(path=IMG_DIR / "feed.png", full_page=False)

        # 5. Profile
        print("→ profile.png")
        page.goto(f"{BASE_URL}/profile/{username}/")
        page.wait_for_timeout(600)
        page.screenshot(path=IMG_DIR / "profile.png", full_page=False)

        # 6. Post detail (primeiro post do feed)
        print("→ post-detail.png")
        page.goto(f"{BASE_URL}/feed/")
        first_post = page.locator("a[href*='/post/']").first
        if first_post.count():
            first_post.click()
            page.wait_for_timeout(600)
        else:
            print("  Sem posts no feed — a usar página de feed como fallback")
        page.screenshot(path=IMG_DIR / "post-detail.png", full_page=False)

        browser.close()

    print("\nScreenshots guardados em:", IMG_DIR)
    for f in sorted(IMG_DIR.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screenshots do ant.social")
    parser.add_argument("--username", default="admin", help="Username para login")
    parser.add_argument("--password", default="admin", help="Password para login")
    args = parser.parse_args()
    take_screenshots(args.username, args.password)
