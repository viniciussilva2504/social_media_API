"""
Generate the Open Graph preview image for ant.social.

Replicates the exact CSS flex-wrap layout of the morse-code logo
(hero version: justify-content: flex-end, right-aligned rows).
White background, no text, no decorative band.

Output: static/og-image.png (1200x630)

Usage:
    python generate_og_image.py

Requires Pillow >= 8.2:
    pip install Pillow
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Pillow not found. Run: pip install Pillow")

# ── Canvas ──────────────────────────────────────────────────────────────────
W, H = 1200, 630
img = Image.new("RGB", (W, H), "#ffffff")
draw = ImageDraw.Draw(img)

# ── Brand colours ────────────────────────────────────────────────────────────
RED    = "#cc2200"  # mc1
BLUE   = "#003d99"  # mc2
YELLOW = "#c89610"  # mc3

# ── Scale — mirrors hero CSS values × 10 ─────────────────────────────────────
# hero: dot 6px, dash 16×6px, gap 2px, sep 4px, container 60px
SCALE  = 10
DOT_W  = 6  * SCALE   # 72px — circle diameter
DOT_H  = 6  * SCALE   # 72px
DASH_W = 16 * SCALE   # 192px wide pill
DASH_H = 6  * SCALE   # 72px
SEP_W  = 4  * SCALE   # 48px — transparent letter separator (ms)
GAP    = 2  * SCALE   # 24px — flex gap
CONT_W = 60 * SCALE   # 720px — container width (60px × 12)

# ── Element sequence — matches base.html hero morse exactly ──────────────────
# (type, colour)  type: "dot" | "dash" | "sep" | "break"
# "sep"   = ms span: transparent spacer between letters
# "break" = mw span: width:100% height:0 → forces line wrap, no visual height
MORSE = [
    # A: . –
    ("dot",  RED),    ("dash", BLUE),   ("sep",  None),
    # N: – .
    ("dash", YELLOW), ("dot",  RED),    ("sep",  None),
    # T: –
    ("dash", BLUE),
    # word break (period separator)
    ("break", None),
    # S: . . .
    ("dot",  YELLOW), ("dot",  RED),    ("dot",  BLUE),   ("sep", None),
    # O: – – –
    ("dash", YELLOW), ("dash", RED),    ("dash", BLUE),   ("sep", None),
    # C: – . – .
    ("dash", YELLOW), ("dot",  RED),    ("dash", BLUE),   ("dot", YELLOW), ("sep", None),
    # I: . .
    ("dot",  RED),    ("dot",  BLUE),   ("sep",  None),
    # A: . –
    ("dot",  YELLOW), ("dash", RED),    ("sep",  None),
    # L: . – . .
    ("dot",  BLUE),   ("dash", YELLOW), ("dot",  RED),    ("dot", BLUE),
]


def item_width(t):
    if t == "dot":   return DOT_W
    if t == "dash":  return DASH_W
    if t == "sep":   return SEP_W
    return 0


# ── Simulate CSS flex-wrap (left-to-right, wrap when row exceeds CONT_W) ─────
rows = []
current_row = []
current_w = 0

for typ, colour in MORSE:
    if typ == "break":
        if current_row:
            rows.append(current_row)
            current_row = []
            current_w = 0
        continue

    w = item_width(typ)

    if current_w == 0:
        current_row.append((typ, colour, w))
        current_w = w
    elif current_w + GAP + w <= CONT_W:
        current_row.append((typ, colour, w))
        current_w += GAP + w
    else:
        rows.append(current_row)
        current_row = [(typ, colour, w)]
        current_w = w

if current_row:
    rows.append(current_row)


# ── Compute logo bounding box ─────────────────────────────────────────────────
n_rows     = len(rows)
logo_h     = n_rows * DOT_H + (n_rows - 1) * GAP
x0         = (W - CONT_W) // 2   # centre container horizontally
y0         = (H - logo_h) // 2   # centre block vertically


# ── Draw (justify-content: flex-end — items right-aligned in each row) ────────
y = y0
for row in rows:
    row_w = sum(w for _, _, w in row) + GAP * (len(row) - 1)
    x = x0 + (CONT_W - row_w)   # right-align within container

    for i, (typ, colour, w) in enumerate(row):
        if colour == "sep" or typ == "sep":
            pass  # transparent spacer — no drawing
        elif typ == "dot":
            draw.ellipse([x, y, x + DOT_W, y + DOT_H], fill=colour)
        elif typ == "dash":
            draw.rounded_rectangle(
                [x, y, x + DASH_W, y + DASH_H],
                radius=DOT_H // 2,
                fill=colour,
            )
        x += w + (GAP if i < len(row) - 1 else 0)

    y += DOT_H + GAP


# ── Save ──────────────────────────────────────────────────────────────────────
out = Path("static/og-image.png")
img.save(out, "PNG", optimize=True)
print(f"✓ Saved {out}  ({W}×{H}px)  —  {n_rows} rows, logo {CONT_W}×{logo_h}px")
