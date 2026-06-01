#!/usr/bin/env python3
"""Fit manifest coordinates and font sizes to source_bbox_px annotations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5


def resolve_path(base: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def resolve_source(manifest_path: Path, manifest: dict[str, Any], slide: dict[str, Any], override: Path | None) -> Path:
    if override:
        return override
    base = manifest_path.parent
    for raw in (manifest.get("source_image"), slide.get("source_image"), slide.get("background")):
        candidate = resolve_path(base, raw)
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError("No source image found. Pass --source or set source_image/background in the manifest.")


def windows_font_path(bold: bool) -> str | None:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def font_at_size(size_pt: float, image_width: int, slide_w: float, bold: bool) -> ImageFont.ImageFont:
    px_size = max(6, int(round(size_pt * image_width / slide_w / 72)))
    font_path = windows_font_path(bold)
    if font_path:
        return ImageFont.truetype(font_path, px_size)
    return ImageFont.load_default()


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def fits(draw: ImageDraw.ImageDraw, box: dict[str, Any], size_pt: float, bbox: list[int], image_width: int, slide_w: float) -> bool:
    _, _, bw, bh = bbox
    font = font_at_size(size_pt, image_width, slide_w, bool(box.get("bold", False)))
    margin_px = int(round(float(box.get("margin", 0)) * image_width / slide_w))
    usable_w = max(1, bw - margin_px * 2)
    usable_h = max(1, bh - margin_px * 2)
    lines = str(box.get("text", "")).splitlines() or [""]
    max_w = max(text_bbox(draw, line, font)[0] for line in lines)
    _, line_h_raw = text_bbox(draw, "国Ag", font)
    line_h = math.ceil(line_h_raw * float(box.get("line_spacing", 1.12)))
    total_h = line_h * max(1, len(lines))
    return max_w <= usable_w and total_h <= usable_h


def fit_size(draw: ImageDraw.ImageDraw, box: dict[str, Any], bbox: list[int], image_width: int, slide_w: float) -> float:
    upper = float(box.get("font_size", 12))
    lower = float(box.get("min_font_size", 6.5))
    size = upper
    while size > lower:
        if fits(draw, box, size, bbox, image_width, slide_w):
            return round(size, 1)
        size -= 0.2
    return round(lower, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit manifest fields to source_bbox_px annotations.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    slide_size = manifest.get("slide_size") or {}
    slide_w = float(slide_size.get("width", SLIDE_W_IN))
    slide_h = float(slide_size.get("height", SLIDE_H_IN))
    if str(manifest.get("units", "inches")).lower() != "inches":
        raise ValueError("This fitter currently expects manifest units='inches'.")

    slide = manifest["slides"][0]
    source_path = resolve_source(args.manifest, manifest, slide, args.source)
    source = Image.open(source_path).convert("RGB")
    draw = ImageDraw.Draw(source)
    image_w, image_h = source.size

    for box in slide.get("text_boxes", []):
        bbox = box.get("source_bbox_px")
        if not bbox:
            continue
        x, y, w, h = [float(v) for v in bbox]
        box["x"] = round(x / image_w * slide_w, 3)
        box["y"] = round(y / image_h * slide_h, 3)
        box["w"] = round(w / image_w * slide_w, 3)
        box["h"] = round(h / image_h * slide_h, 3)
        box["font_size"] = fit_size(draw, box, [int(x), int(y), int(w), int(h)], image_w, slide_w)
        box["render_anchor"] = "glyph_bbox"
        box["alignment_status"] = "bbox-fit"

    manifest["phase"] = "ppt-to-editable-source-bbox-fit"
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + " Round 3 mechanically fits coordinates and font sizes to source_bbox_px."
    ).strip()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
