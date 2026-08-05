"""
Render a small terminal "system info" panel as a self-animating SVG.

Each row fades/slides in with a staggered delay so the panel appears to
type itself out. Set PREVIEW=1 to render every row already visible, for
checking the design in a normal image viewer.
"""
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "sysinfo.svg")

ROWS = [
    ("role", "B.Tech CS Student"),
    ("focus", "AI/ML · Backend Systems"),
    ("stack", "Python · FastAPI · MongoDB"),
    ("now", "Shipping PlacementOS (RAG backend)"),
]

WIDTH = 460
HEADER_H = 40
ROW_H = 34
PAD_X = 20
TOP_PAD = 16

BG = "#0d0d17"
HEADER_BG = "#151524"
ACCENT = "#4dabf7"
LABEL_COLOR = "#6b7280"
VALUE_COLOR = "#e5e7eb"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]


def render(preview: bool = False):
    height = HEADER_H + TOP_PAD + len(ROWS) * ROW_H + TOP_PAD

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8" ry="8" fill="{BG}"/>')

    # Header bar with traffic-light dots
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{HEADER_H}" rx="8" ry="8" fill="{HEADER_BG}"/>')
    parts.append(f'<rect x="0" y="{HEADER_H - 8}" width="{WIDTH}" height="8" fill="{HEADER_BG}"/>')
    for i, color in enumerate(DOT_COLORS):
        parts.append(f'<circle cx="{20 + i * 18}" cy="{HEADER_H // 2}" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="{HEADER_H // 2 + 4}" font-size="11" fill="{LABEL_COLOR}" '
        f'text-anchor="middle">whoami --verbose</text>'
    )

    # Rows
    delay_per_row = 0.5
    for i, (label, value) in enumerate(ROWS):
        y = HEADER_H + TOP_PAD + i * ROW_H + 18
        begin = 0.3 + i * delay_per_row
        opacity_start = "1" if preview else "0"

        group_attrs = ""
        if not preview:
            group_attrs = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-6 0" to="0 0" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
            )

        parts.append(f'<g opacity="{opacity_start}">')
        parts.append(
            f'<text x="{PAD_X}" y="{y}" font-size="12" fill="{ACCENT}">$</text>'
        )
        parts.append(
            f'<text x="{PAD_X + 14}" y="{y}" font-size="12" fill="{LABEL_COLOR}">{label}</text>'
        )
        parts.append(
            f'<text x="{PAD_X + 90}" y="{y}" font-size="12" fill="{VALUE_COLOR}">{value}</text>'
        )
        parts.append(group_attrs)
        parts.append('</g>')

    # Blinking cursor after the last row
    cursor_y = HEADER_H + TOP_PAD + len(ROWS) * ROW_H + 18
    cursor_begin = 0.3 + len(ROWS) * delay_per_row
    parts.append(
        f'<text x="{PAD_X}" y="{cursor_y}" font-size="12" fill="{ACCENT}" opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{cursor_begin:.2f}s" '
        f'dur="0.01s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="1;0;1" dur="1s" '
        f'begin="{cursor_begin:.2f}s" repeatCount="indefinite"/>'
        f'$ _</text>'
    )

    parts.append('</svg>')
    return "".join(parts)


def main():
    preview = os.environ.get("PREVIEW") == "1"
    svg = render(preview=preview)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH} ({len(svg)} bytes){' [preview mode]' if preview else ''}")


if __name__ == "__main__":
    main()
