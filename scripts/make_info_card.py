#!/usr/bin/env python3
"""
make_info_card.py — Neofetch-style profile info card.

Edit the CONTENT list below with your own details, then run:
    python scripts/make_info_card.py

Set STATIC=1 to emit a frozen (non-animated) frame — useful for local
previews that don't support SVG animation (e.g. macOS Quick Look):
    STATIC=1 python scripts/make_info_card.py
"""
import os

OUT_PATH = "info-card.svg"

TITLE = "ankit@github ~"

# --- EDIT ME: this is your story, not your GitHub stats (the ---
# --- heatmap already covers those) -----------------------------
CONTENT = [
    ("Now",        "Full-stack Web and Mobile Developer (MERN / PERN / React Native)"),
    ("Prev",       "5th-sem IT student"),
    ("Stack",      "TypeScript . ReactJS . Node.js . PostgreSQL . MongoDB . React Native"),
    ("Highlights", "Cloud-Desk . Flik . AgriSathi"),
    ("Terminal",   "Arch Linux + Hyprland"),
]

MIN_WIDTH = 490
PADDING = 22
LABEL_COL_W = 92
CHAR_PX = 7.8   # approx monospace advance width at 13px font size
TITLEBAR_H = 34
ROW_H = 30
FONT = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

COL_LABEL = "#7ee787"   # green, like a shell prompt var
COL_VALUE = "#c9d1d9"   # light gray body text
COL_BG = "#0d1117"      # GitHub dark background
COL_BORDER = "#30363d"
COL_DOT_RED = "#ff5f56"
COL_DOT_YEL = "#ffbd2e"
COL_DOT_GRN = "#27c93f"

STAGGER_MS = 160
FADE_MS = 420


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    static = os.environ.get("STATIC") == "1"
    height = TITLEBAR_H + PADDING + len(CONTENT) * ROW_H + PADDING

    longest_value = max((len(v) for _, v in CONTENT), default=0)
    content_width = PADDING + LABEL_COL_W + int(longest_value * CHAR_PX) + PADDING
    width = max(MIN_WIDTH, content_width)

    style = f"""
    text {{ font-family: {FONT}; }}
    .label {{ fill: {COL_LABEL}; font-size: 13px; font-weight: 600; }}
    .value {{ fill: {COL_VALUE}; font-size: 13px; }}
    .title {{ fill: {COL_VALUE}; font-size: 12px; opacity: 0.75; }}
    .row {{
        opacity: 0;
        transform: translateX(-6px);
        animation-name: fade-in;
        animation-duration: {FADE_MS}ms;
        animation-timing-function: ease-out;
        animation-fill-mode: forwards;
    }}
    @keyframes fade-in {{
        from {{ opacity: 0; transform: translateX(-6px); }}
        to   {{ opacity: 1; transform: translateX(0); }}
    }}
    """
    if static:
        style += ".row { opacity: 1 !important; animation: none !important; transform: none !important; }"

    rows_svg = []
    for i, (label, value) in enumerate(CONTENT):
        y = TITLEBAR_H + PADDING + i * ROW_H + 18
        delay = i * STAGGER_MS
        rows_svg.append(
            f'<g class="row" style="animation-delay:{delay}ms">'
            f'<text x="{PADDING}" y="{y}" class="label">{esc(label)}</text>'
            f'<text x="{PADDING + LABEL_COL_W}" y="{y}" class="value">{esc(value)}</text>'
            f'</g>'
        )

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg">
  <style>{style}</style>
  <rect x="0" y="0" width="{width}" height="{height}" rx="10"
        fill="{COL_BG}" stroke="{COL_BORDER}" stroke-width="1" />
  <circle cx="20" cy="{TITLEBAR_H/2}" r="6" fill="{COL_DOT_RED}" />
  <circle cx="40" cy="{TITLEBAR_H/2}" r="6" fill="{COL_DOT_YEL}" />
  <circle cx="60" cy="{TITLEBAR_H/2}" r="6" fill="{COL_DOT_GRN}" />
  <text x="{width/2}" y="{TITLEBAR_H/2 + 4}" text-anchor="middle" class="title">{esc(TITLE)}</text>
  <line x1="0" y1="{TITLEBAR_H}" x2="{width}" y2="{TITLEBAR_H}" stroke="{COL_BORDER}" stroke-width="1" />
  {"".join(rows_svg)}
</svg>'''

    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}{' (static frame)' if static else ''}")


if __name__ == "__main__":
    build_svg()
