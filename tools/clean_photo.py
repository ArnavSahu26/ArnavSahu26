"""
Clean up a source photo so it converts into readable ASCII art instead of
mid-gray mush.

Pipeline:
  1. Cut the background with rembg so only the subject remains.
  2. Even out lighting with CLAHE (adaptive histogram equalization).
  3. Composite onto a white canvas so background falls at the LIGHT end
     of the character ramp, not the dark end.

Usage:
    python tools/clean_photo.py path/to/photo.jpg
    # writes assets/photo-ready.png
"""
import sys
import os

import numpy as np
from PIL import Image
import cv2
from rembg import remove

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "photo-ready.png")


def remove_background(img: Image.Image) -> Image.Image:
    """Returns an RGBA image with background removed."""
    result = remove(img)
    return result.convert("RGBA")


def apply_clahe(img: Image.Image) -> Image.Image:
    """Apply CLAHE to the luminance channel to pull out shadow/highlight detail."""
    rgb = np.array(img.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_channel)

    merged = cv2.merge((l_eq, a_channel, b_channel))
    rgb_eq = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    return Image.fromarray(rgb_eq)


def composite_on_white(subject_rgba: Image.Image, lit_rgb: Image.Image) -> Image.Image:
    """
    Take the alpha mask from subject_rgba (post background-removal) and the
    lighting-corrected RGB from lit_rgb, composite onto solid white.
    """
    alpha = subject_rgba.split()[-1]
    canvas = Image.new("RGB", subject_rgba.size, (255, 255, 255))
    canvas.paste(lit_rgb, (0, 0), mask=alpha)
    return canvas


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/clean_photo.py <path-to-photo>", file=sys.stderr)
        sys.exit(1)

    src_path = sys.argv[1]
    if not os.path.exists(src_path):
        print(f"File not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(src_path)

    print("Removing background...")
    subject_rgba = remove_background(img)

    print("Applying CLAHE contrast correction...")
    lit_rgb = apply_clahe(subject_rgba)

    print("Compositing onto white canvas...")
    final = composite_on_white(subject_rgba, lit_rgb)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final.save(OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
