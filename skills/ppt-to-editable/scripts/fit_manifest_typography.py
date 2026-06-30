#!/usr/bin/env python3
"""Fit manifest typography to source-image bboxes using role-specific bounds."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SLIDE_W_IN = 13.333333

ROLE_RULES: dict[str, dict[str, float]] = {
    "title": {"min": 24.0, "max": 34.0, "line_spacing": 1.0, "height_fill": 0.95},
    "subtitle": {"min": 11.0, "max": 16.0, "line_spacing": 1.0, "height_fill": 0.90},
    "section": {"min": 12.5, "max": 18.0, "line_spacing": 1.0, "height_fill": 0.92},
    "gate-number": {"min": 11.0, "max": 17.0, "line_spacing": 1.0, "height_fill": 0.90},
    "gate-label": {"min": 9.5, "max": 12.5, "line_spacing": 1.0, "height_fill": 0.88},
    "evidence-header": {"min": 9.5, "max": 12.8, "line_spacing": 1.0, "height_fill": 0.90},
    "evidence-body": {"min": 8.8, "max": 12.0, "line_spacing": 1.06, "height_fill": 0.88},
    "panel-title": {"min": 13.0, "max": 20.0, "line_spacing": 1.0, "height_fill": 0.90},
    "panel-copy": {"min": 8.8, "max": 12.2, "line_spacing": 1.06, "height_fill": 0.88},
    "line-item": {"min": 9.5, "max": 12.4, "line_spacing": 1.0, "height_fill": 0.88},
    "takeaway": {"min": 15.0, "max": 21.0, "line_spacing": 1.0, "height_fill": 0.92},
    "source": {"min": 6.0, "max": 8.0, "line_spacing": 1.0, "height_fill": 0.85},
}


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


def text_extents(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.ImageFont, line_spacing: float) -> tuple[int, int]:
    widths = []
    for line in lines:
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        widths.append(right - left)
    _, top, _, bottom = draw.textbbox((0, 0), "国Ag", font=font)
    line_h = math.ceil((bottom - top) * line_spacing)
    return max(widths or [0]), max(1, line_h * max(1, len(lines)))


def fits(
    draw: ImageDraw.ImageDraw,
    box: dict[str, Any],
    bbox: list[int],
    size_pt: float,
    line_spacing: float,
    image_width: int,
    slide_w: float,
    height_fill: float,
) -> bool:
    _, _, bw, bh = bbox
    font = font_at_size(size_pt, image_width, slide_w, bool(box.get("bold", False)))
    lines = str(box.get("text", "")).splitlines() or [""]
    width, height = text_extents(draw, lines, font, line_spacing)
    return width <= bw and height <= max(1, int(bh * height_fill))


def fit_box(draw: ImageDraw.ImageDraw, box: dict[str, Any], image_width: int, slide_w: float) -> None:
    bbox = box.get("source_bbox_px")
    if not bbox:
        return
    role = str(box.get("role", ""))
    rule = ROLE_RULES.get(role, {"min": 8.0, "max": float(box.get("font_size", 12)), "line_spacing": 1.0, "height_fill": 0.88})
    line_spacing = rule["line_spacing"]
    low = rule["min"]
    high = rule["max"]
    best = low
    for _ in range(32):
        mid = (low + high) / 2
        if fits(draw, box, [int(v) for v in bbox], mid, line_spacing, image_width, slide_w, rule["height_fill"]):
            best = mid
            low = mid
        else:
            high = mid
    box["font_size"] = round(best, 1)
    box["line_spacing"] = line_spacing
    box["render_anchor"] = "glyph_bbox"
    box["alignment_status"] = "typography-fit"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit manifest typography by role and source bbox.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    slide_w = float((manifest.get("slide_size") or {}).get("width", SLIDE_W_IN))
    slide = manifest["slides"][0]
    source_path = resolve_source(args.manifest, manifest, slide, args.source)
    source = Image.open(source_path).convert("RGB")
    draw = ImageDraw.Draw(source)

    for box in slide.get("text_boxes", []):
        fit_box(draw, box, source.size[0], slide_w)

    manifest["phase"] = "ppt-to-editable-typography-fit"
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + " Fit font size and line spacing mechanically by role and source bbox."
    ).strip()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
