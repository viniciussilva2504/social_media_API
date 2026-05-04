"""
Generate the Open Graph preview image for ant.social.
Output: static/og-image.png (1200x630)

Usage:
    python generate_og_image.py

Requires Pillow:
    pip install Pillow
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow not found. Run: pip install Pillow")

# ── Canvas ─────────────────────────────────────────────────────────────────
W, H = 1200, 630
img = Image.new("RGB", (W, H), "#0a0a0a")
draw = ImageDraw.Draw(img)

# ── Brand colours ──────────────────────────────────────────────────────────
RED    = "#cc2200"
BLUE   = "#003d99"
YELLOW = "#c89610"
WHITE  = "#f5f5f5"
GREY   = "#555555"

# ── Bauhaus accent blocks ───────────────────────────────────────────────────
# Three rectangles at the bottom edge (signature Bauhaus horizontal band)
block_h = 14
draw.rectangle([0,       H - block_h, W // 3,       H], fill=RED)
draw.rectangle([W // 3,  H - block_h, (W // 3) * 2, H], fill=BLUE)
draw.rectangle([(W // 3) * 2, H - block_h, W,        H], fill=YELLOW)

# Thin accent line top
draw.rectangle([0, 0, W, 4], fill=BLUE)

# ── Fonts (falls back gracefully if Roboto not installed) ───────────────────
def load_font(size, bold=False):
    candidates = [
        "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf",
        "RobotoFlex-Regular.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()

font_brand   = load_font(128, bold=True)
font_tagline = load_font(38)
font_url     = load_font(26)

# ── "ant.social" — each colour block ───────────────────────────────────────
brand = "ant.social"
colors_brand = [RED, RED, RED, WHITE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE]
# a=RED  n=RED  t=RED  .=WHITE  s=BLUE  o=BLUE  c=BLUE  i=BLUE  a=BLUE  l=BLUE

# Measure total width of brand text to centre it
char_widths = []
for ch in brand:
    bb = draw.textbbox((0, 0), ch, font=font_brand)
    char_widths.append(bb[2] - bb[0])

total_w = sum(char_widths)
x_start = (W - total_w) // 2
y_brand = (H - 200) // 2 - 30  # vertically centred-ish

# Draw each character with its colour
x = x_start
for i, ch in enumerate(brand):
    colour = [RED, RED, RED, WHITE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE][min(i, 9)]
    draw.text((x, y_brand), ch, font=font_brand, fill=colour)
    x += char_widths[i]

# ── Tagline ─────────────────────────────────────────────────────────────────
tagline = "media for non-charismatic people"
bb = draw.textbbox((0, 0), tagline, font=font_tagline)
tw = bb[2] - bb[0]
y_tagline = y_brand + 140
draw.text(((W - tw) // 2, y_tagline), tagline, font=font_tagline, fill=GREY)

# ── URL ─────────────────────────────────────────────────────────────────────
url = "vjsilva250490.pythonanywhere.com"
bb = draw.textbbox((0, 0), url, font=font_url)
uw = bb[2] - bb[0]
y_url = H - 60
draw.text(((W - uw) // 2, y_url), url, font=font_url, fill=GREY)

# ── Save ────────────────────────────────────────────────────────────────────
out = Path("static/og-image.png")
img.save(out, "PNG", optimize=True)
print(f"✓ Saved {out}  ({W}×{H}px)")
