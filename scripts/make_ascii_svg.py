#!/usr/bin/env python3
"""
make_ascii_svg.py — Convert a prepped grayscale photo into a
self-typing, monochrome ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [ascii-portrait.svg]
"""
import os
import sys

from PIL import Image

RAMP = " .`:-=+*cs#%@"           # bright (sparse) -> dark (dense)
COLS = 100
ROWS = 53
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6          # monospace advance width
CHAR_H = FONT_SIZE * 1.15
FILL_COLOR = "#c9d1d9"            # light gray — monochrome on purpose
BG_COLOR = "transparent"
ROW_STAGGER_MS = 45               # delay between each row starting
ROW_DURATION_MS = 380             # how long each row takes to wipe in
TIMING_STEPS = 28                 # typewriter "chunkiness" of the wipe

# Terminal characters are taller than wide, so correct the sampling
# aspect ratio to avoid a squashed portrait.
ASPECT_CORRECTION = 0.55


def image_to_ascii_rows(path: str, cols: int = COLS, rows: int = ROWS):
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows))
    pixels = img.load()

    ramp_len = len(RAMP) - 1
    ascii_rows = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            brightness = pixels[x, y]  # 0 (black) .. 255 (white)
            idx = int((255 - brightness) / 255 * ramp_len)
            row_chars.append(RAMP[idx])
        ascii_rows.append("".join(row_chars))
    return ascii_rows


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(ascii_rows, out_path: str):
    n_rows = len(ascii_rows)
    n_cols = max(len(r) for r in ascii_rows)
    width = n_cols * CHAR_W
    height = n_rows * CHAR_H

    style = f"""
    .ascii-text {{
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-size: {FONT_SIZE}px;
        fill: {FILL_COLOR};
        white-space: pre;
    }}
    .row-clip-rect {{
        animation-timing-function: steps({TIMING_STEPS}, end);
        animation-fill-mode: forwards;
        animation-iteration-count: 1;
    }}
    .cursor {{
        fill: {FILL_COLOR};
        animation-timing-function: steps({TIMING_STEPS}, end);
        animation-fill-mode: forwards;
        animation-iteration-count: 1;
        opacity: 0.9;
    }}
    @keyframes wipe-in {{
        from {{ width: 0px; }}
        to   {{ width: {width}px; }}
    }}
    @keyframes cursor-ride {{
        from {{ transform: translateX(0px); opacity: 0.9; }}
        99%  {{ opacity: 0.9; }}
        to   {{ transform: translateX({width}px); opacity: 0; }}
    }}
    """
    if os.environ.get("STATIC") == "1":
        style += (
            ".row-clip-rect { animation: none !important; width: "
            f"{width}px !important; }} "
            ".cursor { animation: none !important; opacity: 0 !important; }"
        )

    defs = []
    rows_markup = []
    for i, row in enumerate(ascii_rows):
        delay = i * ROW_STAGGER_MS
        clip_id = f"clip-row-{i}"
        y = (i + 1) * CHAR_H - (CHAR_H * 0.25)
        row_y = i * CHAR_H

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect class="row-clip-rect" x="0" y="{row_y}" '
            f'width="0" height="{CHAR_H}" '
            f'style="animation-name: wipe-in; animation-duration: {ROW_DURATION_MS}ms; '
            f'animation-delay: {delay}ms;" />'
            f'</clipPath>'
        )

        rows_markup.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text class="ascii-text" x="0" y="{y}">{esc(row)}</text>'
            f'</g>'
            f'<rect class="cursor" x="0" y="{row_y}" width="{CHAR_W}" height="{CHAR_H}" '
            f'style="animation-name: cursor-ride; animation-duration: {ROW_DURATION_MS}ms; '
            f'animation-delay: {delay}ms;" />'
        )

    svg = (
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<style>{style}</style>'
        f'<defs>{"".join(defs)}</defs>'
        f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="{BG_COLOR}" />'
        f'{"".join(rows_markup)}'
        f'</svg>'
    )

    with open(out_path, "w") as f:
        f.write(svg)
    print(f"Wrote {out_path} ({n_cols}x{n_rows} chars, {width:.0f}x{height:.0f}px)")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    rows = image_to_ascii_rows(src)
    build_svg(rows, out)
