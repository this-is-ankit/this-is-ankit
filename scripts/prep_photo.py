#!/usr/bin/env python3
"""
prep_photo.py — Prepare a photo for ASCII conversion:
    1. Remove the background (rembg) so only the subject is isolated.
    2. Boost local contrast with CLAHE so a flat, evenly-lit face gets
       real highlights and shadows.
    3. Composite onto pure white so the background maps to the blank
       end of the ASCII ramp (white -> space character).
Output: a grayscale source-prepped.png

Usage:
    python scripts/prep_photo.py path/to/source-photo.jpg
"""
import io
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUTPUT_PATH = "source-prepped.png"


def prep_photo(input_path: str, output_path: str = OUTPUT_PATH) -> None:
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with a transparent background
    result_bytes = remove(input_bytes)
    rgba = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    # 2. Composite onto pure white BEFORE contrast work, so CLAHE
    #    isn't fighting with a transparent alpha channel
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. Boost local contrast with CLAHE (contrast-limited adaptive
    #    histogram equalization) — this is what turns a flat, evenly
    #    -lit face into something with real highlights and shadows
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # 4. Re-flatten the background to pure white in case CLAHE
    #    darkened it, using rembg's own alpha mask to know what
    #    counted as background
    alpha = np.array(rgba)[:, :, 3]
    contrasted[alpha < 10] = 255

    Image.fromarray(contrasted).save(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py path/to/source-photo.jpg")
        sys.exit(1)
    prep_photo(sys.argv[1])
