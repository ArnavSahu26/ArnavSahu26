"""
Pull the public contribution calendar for a GitHub user and save it as JSON.

Uses the same HTML fragment endpoint the profile page itself renders from —
no OAuth, no personal access token required.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import httpx
from lxml import html

GITHUB_USERNAME = os.environ.get("GITHUB_PROFILE_USER", "ArnavSahu26")
CONTRIB_URL = f"https://github.com/users/{GITHUB_USERNAME}/contributions"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "contributions.json")

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def fetch_calendar_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0)",
        "Accept": "text/html",
    }
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def parse_calendar(html_text: str) -> list[dict]:
    """
    Parse day cells out of the contribution calendar fragment.

    As of GitHub's current markup, each <td class="ContributionCalendar-day">
    carries data-date and data-level directly, but the actual contribution
    count is NOT an attribute on the cell -- it only appears as text inside a
    sibling <tool-tip for="contribution-day-component-...">, e.g.
    "3 contributions on January 5th." or "No contributions on August 3rd."
    We match each cell to its tooltip via the cell's id / the tooltip's `for`.
    """
    tree = html.fromstring(html_text)
    cells = tree.xpath("//td[@data-date]")

    tooltip_text_by_target = {}
    for tip in tree.xpath("//tool-tip[@for]"):
        target = tip.get("for")
        text = tip.text_content().strip()
        if target:
            tooltip_text_by_target[target] = text

    def count_from_tooltip(text: str) -> int:
        if not text:
            return 0
        first_word = text.strip().split(" ", 1)[0]
        if first_word.lower() == "no":
            return 0
        digits = "".join(ch for ch in first_word if ch.isdigit())
        return int(digits) if digits else 0

    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue

        level_attr = cell.get("data-level")
        level = int(level_attr) if level_attr is not None else None

        cell_id = cell.get("id")
        tooltip_text = tooltip_text_by_target.get(cell_id, "") if cell_id else ""
        count = count_from_tooltip(tooltip_text)

        days.append({"date": date_str, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {
            "total": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "busiest_weekday": None,
            "weekday_totals": {},
        }

    total = sum(d["count"] for d in days)

    # Streaks
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Busiest weekday
    weekday_totals = defaultdict(int)
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday_totals[WEEKDAY_NAMES[dt.weekday()]] += d["count"]

    busiest_weekday = max(weekday_totals, key=weekday_totals.get) if weekday_totals else None

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_weekday": busiest_weekday,
        "weekday_totals": dict(weekday_totals),
    }


def normalize_levels(days: list[dict]) -> list[dict]:
    """
    If data-level wasn't present in the markup, derive a 0-4 level from
    count using simple quantile-ish buckets so rendering still works.
    """
    counts = [d["count"] for d in days if d["level"] is None]
    if not counts:
        return days

    nonzero = sorted(c for c in counts if c > 0)
    if not nonzero:
        for d in days:
            if d["level"] is None:
                d["level"] = 0
        return days

    q1 = nonzero[int(len(nonzero) * 0.25)]
    q2 = nonzero[int(len(nonzero) * 0.5)]
    q3 = nonzero[int(len(nonzero) * 0.75)]

    def level_for(count: int) -> int:
        if count == 0:
            return 0
        if count <= q1:
            return 1
        if count <= q2:
            return 2
        if count <= q3:
            return 3
        return 4

    for d in days:
        if d["level"] is None:
            d["level"] = level_for(d["count"])
    return days


def main():
    try:
        raw_html = fetch_calendar_html(GITHUB_USERNAME)
    except httpx.HTTPError as exc:
        print(f"Failed to fetch contribution calendar: {exc}", file=sys.stderr)
        sys.exit(1)

    days = parse_calendar(raw_html)
    if not days:
        print("Warning: parsed 0 day cells — GitHub's markup may have changed.", file=sys.stderr)

    days = normalize_levels(days)
    stats = compute_stats(days)

    output = {
        "username": GITHUB_USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(days)} day cells to {OUTPUT_PATH}")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
