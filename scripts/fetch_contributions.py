#!/usr/bin/env python3
"""
fetch_contributions.py — Scrape your public GitHub contribution
calendar (no token, no GraphQL API) and write data/contributions.json.

GitHub serves this exact calendar as public HTML at:
    https://github.com/users/<username>/contributions

Usage:
    python scripts/fetch_contributions.py <github-username>

    # or set GITHUB_USERNAME and just run:
    GITHUB_USERNAME=this-is-ankit python scripts/fetch_contributions.py
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

OUT_PATH = "data/contributions.json"
USER_AGENT = (
    "Mozilla/5.0 (compatible; profile-readme-bot/1.0; "
    "+https://github.com)"
)


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    """
    Each day is a <td class="ContributionCalendar-day" data-date="..."
    data-level="0-4" id="contribution-day-component-W-D"> with no inner
    text — the actual "N contributions on <date>" sentence lives in a
    sibling <tool-tip for="<that id>">. We join the two by id.
    """
    soup = BeautifulSoup(html, "html.parser")

    tooltip_by_id = {}
    for tip in soup.find_all("tool-tip"):
        target_id = tip.get("for")
        if target_id:
            tooltip_by_id[target_id] = tip.get_text(strip=True)

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        cell_id = cell.get("id")
        iso_date = cell.get("data-date")
        level = cell.get("data-level")
        if not iso_date or level is None:
            continue

        tooltip_text = tooltip_by_id.get(cell_id, "")
        match = re.search(r"(\d+)\s+contribution", tooltip_text)
        count = int(match.group(1)) if match else 0

        days.append({
            "date": iso_date,
            "level": int(level),
            "count": count,
        })

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    # Longest streak of consecutive days with count > 0
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    # Current streak: walk backwards from the most recent day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": date.today().isoformat(),
    }


def main():
    username = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("GITHUB_USERNAME")
    )
    if not username:
        print("Usage: python scripts/fetch_contributions.py <github-username>")
        sys.exit(1)

    html = fetch_html(username)
    days = parse_days(html)
    if not days:
        print("Warning: parsed 0 day cells — GitHub may have changed its "
              "markup, or the username has no public calendar.")

    stats = compute_stats(days)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"username": username, "days": days, "stats": stats}, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(days)} days, "
          f"{stats['total_contributions']} total contributions, "
          f"current streak {stats['current_streak']}, "
          f"longest streak {stats['longest_streak']}.")


if __name__ == "__main__":
    main()
