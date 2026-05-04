"""
Generate the Open Graph preview image for ant.social.

Draws the actual morse-code logo (dots + dashes) in the Bauhaus
primary colours, two rows (ANT / SOCIAL), white background.

Output: static/og-image.png (1200x630)

Usage:
    python generate_og_image.py

Requires Pillow >= 8.2:
    pip install Pillow
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow not found. Run: pip install Pillow")

# ── Canvas ──────────────────────────────────────────────────────────────────
W, H = 1200, 630
img = Image.new("RGB", (W, H), "#ffffff")
draw = ImageDraw.Draw(img)

# ── Brand colours (match CSS variables) ─────────────────────────────────────
RED    = "#cc2200"
BLUE   = "#003d99"
YELLOW = "#c89610"
GREY   = "#888888"

# ── Morse element sizes ──────────────────────────────────────────────────────
DOT_D      = 26   # dot: circle diameter (px)
DASH_W     = 66   # dash: pill width (px)
DASH_H     = 26   # dash: pill height (same as dot for uniformity)
ELEM_GAP   = 8    # gap between elements within one letter
LETTER_GAP = 20   # gap between letters within a row
ROW_GAP    = 54   # vertical gap between ANT row and SOCIAL row

# ── Morse sequences ──────────────────────────────────────────────────────────
# From templates/base.html — (type, colour) per element
# mc1=RED  mc2=BLUE  mc3=YELLOW
ANT = [
    [("dot", RED),    ("dash", BLUE)],                                     # A: . -
    [("dash", YELLOW), ("dot", RED)],                                      # N: - .
    [("dash", BLUE)],                                                      # T: -
]

SOCIAL = [
    [("dot", YELLOW), ("dot", RED),   ("dot", BLUE)],                      # S: . . .
    [("dash", YELLOW), ("dash", RED), ("dash", BLUE)],                     # O: - - -
    [("dash", YELLOW), ("dot", RED),  ("dash", BLUE), ("dot", YELLOW)],    # C: - . - .
    [("dot", RED),    ("dot", BLUE)],                                      # I: . .
    [("dot", YELLOW), ("dash", RED)],                                      # A: . -
    [("dot", BLUE), ("dash", YELLOW), ("dot", RED), ("dot", BLUE)],        # L: . - . .
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def letter_width(letter):
    """Pixel width of a single morse letter (elements + inner gaps)."""
    w = sum(DOT_D if t == "dot" else DASH_W for t, _ in letter)
    w += ELEM_GAP * (len(letter) - 1)
    return w


def row_pixel_width(letters):
    return sum(letter_width(l) for l in letters) + LETTER_GAP * (len(letters) - 1)


def draw_letter(x, y_center, letter):
    """Draw all elements of a morse letter; return x after last element."""
    for i, (typ, colour) in enumerate(letter):
        if typ == "dot":
            top = y_center - DOT_D // 2
            draw.ellipse([x, top, x + DOT_D, top + DOT_D], fill=colour)
            x += DOT_D
        else:
            top = y_center - DASH_H // 2
            draw.rounded_rectangle(
                [x, top, x + DASH_W, top + DASH_H],
                radius=DASH_H // 2,
                fill=colour,
            )
            x += DASH_W
        if i < len(letter) - 1:
            x += ELEM_GAP
    return x


def draw_row(letters, y_center):
    """Draw a full row of morse letters, horizontally centred."""
    total_w = row_pixel_width(letters)
    x = (W - total_w) // 2
    for i, letter in enumerate(letters):
        x = draw_letter(x, y_center, letter)
        if i < len(letters) - 1:
            x += LETTER_GAP


# ── Layout ───────────────────────────────────────────────────────────────────
ROW_H        = DOT_D   # each row is as tall as a dot/dash
TEXT_ABOVE   = 28      # padding above tagline
TAGLINE_SIZE = 26
BAND_H       = 10      # bottom coloured band height

total_content_h = ROW_H + ROW_GAP + ROW_H + TEXT_ABOVE + TAGLINE_SIZE + 20
y_offset = (H - total_content_h) // 2

y_ant    = y_offset + ROW_H // 2
y_social = y_ant + ROW_GAP + ROW_H

# ── Draw the two morse rows ──────────────────────────────────────────────────
draw_row(ANT,    y_ant)
draw_row(SOCIAL, y_social)

# ── "ant.social" tagline below ───────────────────────────────────────────────
def load_font(size, bold=False):
    for name in (
        "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


font_tag = load_font(TAGLINE_SIZE)
tagline  = "ant.social"
bb       = draw.textbbox((0, 0), tagline, font=font_tag)
tw       = bb[2] - bb[0]
y_tag    = y_social + ROW_H // 2 + TEXT_ABOVE
draw.text(((W - tw) // 2, y_tag), tagline, font=font_tag, fill=GREY)

# ── Bauhaus bottom band ──────────────────────────────────────────────────────
draw.rectangle([0,          H - BAND_H, W // 3,       H], fill=RED)
draw.rectangle([W // 3,     H - BAND_H, (W // 3) * 2, H], fill=BLUE)
draw.rectangle([(W // 3)*2, H - BAND_H, W,             H], fill=YELLOW)

# ── Save ─────────────────────────────────────────────────────────────────────
out = Path("static/og-image.png")
img.save(out, "PNG", optimize=True)
print(f"✓ Saved {out}  ({W}×{H}px)")
