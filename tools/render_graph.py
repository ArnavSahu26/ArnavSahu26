"""
Render the pulled contribution data as a self-animating SVG grid.

Squares reveal column-by-column (i.e. week-by-week) using SMIL <animate>
tags on each rect's opacity, so the whole thing plays once when the image
loads and then holds still -- no JS, no external stylesheet.
"""
import json
import os
from collections import defaultdict
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "contributions.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "graph.svg")

LEVELS = ["#1a1a2e", "#16537e", "#1c7ed6", "#4dabf7", "#a5d8ff"]

CELL = 11
GAP = 4
STEP = CELL + GAP
LEFT_PAD = 30
TOP_PAD = 30
BOTTOM_PAD = 46
RIGHT_PAD = 16

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Mon=0 ... Sun=6, sparse labels


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def bucket_into_weeks(days):
    """
    Group days into week-columns the way GitHub's calendar does: columns run
    Sunday-to-Saturday, oldest week first.
    """
    if not days:
        return []

    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        parsed.append((dt, d))
    parsed.sort(key=lambda x: x[0])

    weeks = []
    current_week = [None] * 7
    week_start = None

    for dt, d in parsed:
        py_weekday = dt.weekday()  # Mon=0 ... Sun=6
        sun_indexed = (py_weekday + 1) % 7  # Sun=0 ... Sat=6

        if week_start is None:
            week_start = dt
        elif sun_indexed == 0 and any(current_week):
            weeks.append(current_week)
            current_week = [None] * 7

        current_week[sun_indexed] = {**d, "_dt": dt}

    if any(current_week):
        weeks.append(current_week)

    return weeks


def month_label_positions(weeks):
    """Return {week_index: month_name} for the first week each month appears."""
    labels = {}
    seen_months = set()
    for i, week in enumerate(weeks):
        for cell in week:
            if cell is None:
                continue
            key = (cell["_dt"].year, cell["_dt"].month)
            if key not in seen_months:
                seen_months.add(key)
                labels[i] = MONTH_NAMES[cell["_dt"].month - 1]
            break
    return labels


def render(data):
    days = data["days"]
    stats = data["stats"]
    username = data.get("username", "")

    weeks = bucket_into_weeks(days)
    n_weeks = len(weeks)
    month_labels = month_label_positions(weeks)

    width = LEFT_PAD + n_weeks * STEP + RIGHT_PAD
    height = TOP_PAD + 7 * STEP + BOTTOM_PAD

    svg_parts = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0d0d17"/>'
    )

    # Weekday row labels
    for wd_idx, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + wd_idx * STEP + CELL - 2
        svg_parts.append(
            f'<text x="{LEFT_PAD - 8}" y="{y}" font-size="9" fill="#6b7280" '
            f'text-anchor="end">{label}</text>'
        )

    # Month column labels
    for week_idx, label in month_labels.items():
        x = LEFT_PAD + week_idx * STEP
        svg_parts.append(
            f'<text x="{x}" y="{TOP_PAD - 10}" font-size="9" fill="#6b7280">{label}</text>'
        )

    # Day squares, animated in column by column
    delay_per_week = 0.045
    for week_idx, week in enumerate(weeks):
        col_delay = week_idx * delay_per_week
        for wd_idx, cell in enumerate(week):
            x = LEFT_PAD + week_idx * STEP
            y = TOP_PAD + wd_idx * STEP
            if cell is None:
                continue
            level = cell.get("level") or 0
            level = max(0, min(level, len(LEVELS) - 1))
            color = LEVELS[level]
            title = f'{cell["count"]} contributions on {cell["date"]}'
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" '
                f'fill="{color}" opacity="0">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{col_delay:.3f}s" dur="0.25s" fill="freeze"/>'
                f'</rect>'
            )

    # Legend, bottom-left
    legend_y = height - 20
    svg_parts.append(
        f'<text x="{LEFT_PAD}" y="{legend_y}" font-size="9" fill="#6b7280">Less</text>'
    )
    lx = LEFT_PAD + 32
    for i, color in enumerate(LEVELS):
        svg_parts.append(
            f'<rect x="{lx + i * (CELL + 3)}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" '
            f'rx="2" ry="2" fill="{color}"/>'
        )
    svg_parts.append(
        f'<text x="{lx + len(LEVELS) * (CELL + 3) + 6}" y="{legend_y}" font-size="9" '
        f'fill="#6b7280">More</text>'
    )

    # Stats summary, bottom-right
    summary = (
        f'{stats["total"]} contributions · '
        f'{stats["longest_streak"]}-day best streak · '
        f'busiest day {stats.get("busiest_weekday") or "--"}'
    )
    svg_parts.append(
        f'<text x="{width - RIGHT_PAD}" y="{legend_y}" font-size="9" fill="#8b8fa3" '
        f'text-anchor="end">{summary}</text>'
    )

    svg_parts.append('</svg>')
    return "".join(svg_parts)


def main():
    data = load_data()
    svg = render(data)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
