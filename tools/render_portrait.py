"""
Convert assets/photo-ready.png into a monochrome ASCII-art SVG that draws
itself in top-to-bottom, row by row, using clip-rect animation.

Run tools/clean_photo.py first to produce assets/photo-ready.png.
"""
import os

import numpy as np
from PIL import Image

INPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "photo-ready.png")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "portrait.svg")

# Left = light/empty, right = dense/dark
GLYPHS = " '.,:;~+*xXO#"

COLS = 70          # character grid width
CHAR_W = 6.2        # px per character cell, horizontally
CHAR_H = 11          # px per character cell, vertically
FONT_SIZE = 11

BG_COLOR = "#0d0d17"
FILL_COLOR = "#4dabf7"   # single accent color -- multi-color ASCII reads as clutter

ROW_STAGGER = 0.04   # seconds between each row's reveal, per the walkthrough's ~40ms guidance
ROW_DURATION = 0.25


def load_grayscale_grid(path: str, cols: int):
    img = Image.open(path).convert("L")
    w, h = img.size
    # Character cells are taller than wide, so compensate the aspect ratio
    aspect_correction = CHAR_H / (CHAR_W * 2)
    rows = max(1, int(cols * (h / w) * aspect_correction))

    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small, dtype=np.float32)
    return arr, cols, rows


def brightness_to_glyph(value: float) -> str:
    # value: 0 (black) .. 255 (white). We want dark pixels -> dense glyphs.
    inv = 255 - value
    idx = int((inv / 255) * (len(GLYPHS) - 1))
    idx = max(0, min(idx, len(GLYPHS) - 1))
    glyph = GLYPHS[idx]
    if glyph == "&":
        glyph = "&amp;"
    elif glyph == "<":
        glyph = "&lt;"
    elif glyph == ">":
        glyph = "&gt;"
    return glyph


def render(arr, cols, rows):
    width = cols * CHAR_W + 20
    height = rows * CHAR_H + 20

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    parts.append(f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="{BG_COLOR}"/>')

    for r in range(rows):
        row_chars = []
        for c in range(cols):
            row_chars.append(brightness_to_glyph(arr[r, c]))
        row_text = "".join(row_chars)

        y = 10 + (r + 1) * CHAR_H
        clip_id = f"clip-row-{r}"
        begin = r * ROW_STAGGER

        row_width = cols * CHAR_W

        parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - CHAR_H}" width="0" height="{CHAR_H + 4}">'
            f'<animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DURATION}s" fill="freeze"/>'
            f'</rect>'
            f'</clipPath>'
        )
        parts.append(
            f'<text x="10" y="{y}" font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'clip-path="url(#{clip_id})" xml:space="preserve">{row_text}</text>'
        )

    parts.append('</svg>')
    return "".join(parts)


def main():
    if not os.path.exists(INPUT_PATH):
        print(
            f"Expected cleaned photo at {INPUT_PATH}. "
            f"Run tools/clean_photo.py <your-photo> first.",
        )
        raise SystemExit(1)

    arr, cols, rows = load_grayscale_grid(INPUT_PATH, COLS)
    svg = render(arr, cols, rows)

    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH} ({rows} rows x {cols} cols, {len(svg)} bytes)")


if __name__ == "__main__":
    main()
