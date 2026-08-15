#!/usr/bin/env python3
"""
render_heatmap_svg.py — Render data/contributions.json as an animated
53-week x 7-day contribution calendar SVG.

Usage:
    python scripts/render_heatmap_svg.py

Set STATIC=1 to emit a frozen (non-animated) frame — useful for local
previews that don't support SVG animation:
    STATIC=1 python scripts/render_heatmap_svg.py
"""
import json
import os
from datetime import date

IN_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

# none -> brightest. Level 5 is a neon top end reserved for your
# single highest-contribution day, not something GitHub itself sends.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_LABEL_W = 28
TOP_LABEL_H = 18
LEGEND_H = 26
FOOTER_H = 22
OUTER_PAD = 14

WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # sunday-indexed (0=Sun)
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DIAG_STEP_MS = 9         # delay added per (week+day) diagonal step
CELL_FADE_MS = 300
BG = "transparent"
TEXT_COLOR = "#8b949e"


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def level_for_day(day, max_count):
    base_level = day["level"]
    if max_count > 0 and day["count"] == max_count and base_level >= 4:
        return 5
    return base_level


def month_label_columns(days):
    """Return {week_index: 'Mon'} the first time each month appears."""
    labels = {}
    seen_months = set()
    for i, d in enumerate(days):
        week = i // 7
        month_key = d["date"][:7]
        if month_key not in seen_months:
            seen_months.add(month_key)
            month_num = int(d["date"][5:7])
            labels[week] = MONTH_NAMES[month_num - 1]
    return labels


def build_svg(payload):
    days = payload["days"]
    stats = payload["stats"]
    username = payload.get("username", "")
    weeks = (len(days) + 6) // 7
    max_count = max((d["count"] for d in days), default=0)

    grid_w = LEFT_LABEL_W + weeks * STEP
    width = OUTER_PAD * 2 + grid_w
    height = (OUTER_PAD * 2 + TOP_LABEL_H + 7 * STEP
              + LEGEND_H + FOOTER_H)

    month_labels = month_label_columns(days)

    style = f"""
    text {{
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        fill: {TEXT_COLOR};
    }}
    .day-cell {{
        opacity: 0;
        transform: translateY(-6px);
        animation-name: cell-in;
        animation-duration: {CELL_FADE_MS}ms;
        animation-timing-function: ease-out;
        animation-fill-mode: forwards;
    }}
    @keyframes cell-in {{
        from {{ opacity: 0; transform: translateY(-6px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    """
    if os.environ.get("STATIC") == "1":
        style += ".day-cell { opacity: 1 !important; animation: none !important; transform: none !important; }"

    parts = []
    parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{BG}" />'
    )

    grid_x0 = OUTER_PAD + LEFT_LABEL_W
    grid_y0 = OUTER_PAD + TOP_LABEL_H

    # Month labels along the top
    for week, label in month_labels.items():
        x = grid_x0 + week * STEP
        parts.append(
            f'<text x="{x}" y="{OUTER_PAD + TOP_LABEL_H - 5}" '
            f'font-size="10">{esc(label)}</text>'
        )

    # Weekday labels down the left
    for wd, label in WEEKDAY_LABELS.items():
        y = grid_y0 + wd * STEP + CELL - 1
        parts.append(
            f'<text x="{OUTER_PAD}" y="{y}" font-size="9">{esc(label)}</text>'
        )

    # Day cells, staggered diagonally (week + weekday) top-left to
    # bottom-right so the reveal reads as a sliding diagonal wave.
    for i, d in enumerate(days):
        week = i // 7
        wd = i % 7
        level = level_for_day(d, max_count)
        color = PALETTE[level]
        x = grid_x0 + week * STEP
        y = grid_y0 + wd * STEP
        delay = (week + wd) * DIAG_STEP_MS
        title = f'{d["count"]} contributions on {d["date"]}' if d["count"] \
            else f'No contributions on {d["date"]}'
        parts.append(
            f'<rect class="day-cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}" style="animation-delay:{delay}ms">'
            f'<title>{esc(title)}</title>'
            f'</rect>'
        )

    # Legend: Less -> More
    legend_y = grid_y0 + 7 * STEP + 16
    legend_x = grid_x0
    parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" font-size="9">Less</text>')
    for i, color in enumerate(PALETTE):
        sx = legend_x + 32 + i * (CELL + 3)
        parts.append(
            f'<rect x="{sx}" y="{legend_y}" width="{CELL-1}" height="{CELL-1}" '
            f'rx="2" fill="{color}" />'
        )
    more_x = legend_x + 32 + len(PALETTE) * (CELL + 3) + 4
    parts.append(f'<text x="{more_x}" y="{legend_y + 8}" font-size="9">More</text>')

    # Stats footer
    footer_y = legend_y + LEGEND_H
    footer_text = (
        f'{stats["total_contributions"]} contributions in the last year '
        f'&#183; current streak {stats["current_streak"]}d '
        f'&#183; longest streak {stats["longest_streak"]}d'
    )
    parts.append(
        f'<text x="{grid_x0}" y="{footer_y}" font-size="10">{footer_text}</text>'
    )

    svg = (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<title>{esc(username)} contribution calendar</title>'
        f'<style>{style}</style>'
        f'{"".join(parts)}'
        f'</svg>'
    )
    return svg


def main():
    with open(IN_PATH) as f:
        payload = json.load(f)
    svg = build_svg(payload)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
