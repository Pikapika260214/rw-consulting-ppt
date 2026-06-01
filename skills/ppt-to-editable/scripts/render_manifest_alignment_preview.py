#!/usr/bin/env python3
"""Render text-layout manifest alignment previews for editable PPT workflows."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
DEFAULT_MODES = ("boxes", "faded", "text-only")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def scale_box(box: dict[str, Any], units: str, image_size: tuple[int, int]) -> tuple[int, int, int, int]:
    w_px, h_px = image_size
    if units == "normalized":
        x = float(box["x"]) * w_px
        y = float(box["y"]) * h_px
        w = float(box["w"]) * w_px
        h = float(box["h"]) * h_px
    else:
        slide_w = float(box.get("slide_width", SLIDE_W_IN))
        slide_h = float(box.get("slide_height", SLIDE_H_IN))
        x = float(box["x"]) / slide_w * w_px
        y = float(box["y"]) / slide_h * h_px
        w = float(box["w"]) / slide_w * w_px
        h = float(box["h"]) / slide_h * h_px
    return tuple(round(v) for v in (x, y, w, h))


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


def font_for_box(box: dict[str, Any], image_width: int) -> ImageFont.ImageFont:
    slide_w = float(box.get("slide_width", SLIDE_W_IN))
    px_per_in = image_width / slide_w
    px_size = max(8, int(round(float(box.get("font_size", 12)) * px_per_in / 72)))
    font_path = windows_font_path(bool(box.get("bold", False)))
    if font_path:
        return ImageFont.truetype(font_path, px_size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, tracking_px: float = 0.0) -> tuple[int, int]:
    if not text:
        return (0, 0)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left + max(0, len(text) - 1) * tracking_px, bottom - top


def draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    tracking_px: float,
) -> None:
    x, y = xy
    if tracking_px == 0 or len(text) <= 1:
        draw.text((x, y), text, fill=fill, font=font)
        return
    cursor = x
    for ch in text:
        draw.text((cursor, y), ch, fill=fill, font=font)
        left, top, right, bottom = draw.textbbox((0, 0), ch, font=font)
        cursor += right - left + tracking_px


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    no_wrap: bool = False,
    tracking_px: float = 0.0,
) -> list[str]:
    output: list[str] = []
    for raw_line in str(text).splitlines() or [""]:
        if no_wrap:
            output.append(raw_line)
            continue
        if not raw_line:
            output.append("")
            continue
        tokens = raw_line.split(" ") if " " in raw_line else list(raw_line)
        line = ""
        for token in tokens:
            candidate = token if not line else (f"{line} {token}" if " " in raw_line else f"{line}{token}")
            if text_size(draw, candidate, font, tracking_px)[0] <= max_width or not line:
                line = candidate
            else:
                output.append(line)
                line = token
        if line:
            output.append(line)
    return output


def draw_text_box(draw: ImageDraw.ImageDraw, box: dict[str, Any], rect: tuple[int, int, int, int], image_width: int) -> None:
    x, y, w, h = rect
    font = font_for_box(box, image_width)
    color = "#" + str(box.get("color", "111111")).strip().lstrip("#")[:6]
    margin = int(round(float(box.get("margin", 0)) * image_width / SLIDE_W_IN))
    tracking_px = float(box.get("character_spacing", 0.0)) * image_width / SLIDE_W_IN / 72
    shift_x, shift_y = box.get("text_shift_px", [0, 0])
    shift_x = float(shift_x)
    shift_y = float(shift_y)
    anchor = str(box.get("render_anchor", "box_frame")).lower()
    line_spacing = float(box.get("line_spacing", 1.14))
    tx = x + margin
    ty = y + margin
    usable_w = max(1, w - margin * 2)
    lines = wrap_text(draw, str(box.get("text", "")), font, usable_w, no_wrap=bool(box.get("no_wrap", False)), tracking_px=tracking_px)
    _, line_h_raw = text_size(draw, "国Ag", font, tracking_px)
    line_h = max(1, int(math.ceil(line_h_raw * line_spacing)))
    align = str(box.get("align", "left")).lower()
    for idx, line in enumerate(lines):
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        line_w = right - left + max(0, len(line) - 1) * tracking_px
        lx = tx
        if align == "center":
            lx = x + (w - line_w) / 2
        elif align == "right":
            lx = x + w - margin - line_w
        ly = ty + idx * line_h
        if anchor == "glyph_bbox":
            lx -= left
            ly -= top
        lx += shift_x
        ly += shift_y
        if ly > y + h:
            break
        draw_tracked_text(draw, (lx, ly), line, font=font, fill=color, tracking_px=tracking_px)


def draw_preview(
    source: Image.Image,
    manifest: dict[str, Any],
    slide: dict[str, Any],
    mode: str,
) -> Image.Image:
    units = str(manifest.get("units", "inches")).lower()
    boxes = slide.get("text_boxes") or []
    if mode == "text-only":
        canvas = Image.new("RGB", source.size, "white")
    elif mode == "faded":
        white = Image.new("RGB", source.size, "white")
        canvas = Image.blend(source.convert("RGB"), white, 0.68)
    else:
        canvas = source.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)

    for idx, box in enumerate(boxes, start=1):
        enriched = dict(box)
        enriched["slide_width"] = float((manifest.get("slide_size") or {}).get("width", SLIDE_W_IN))
        enriched["slide_height"] = float((manifest.get("slide_size") or {}).get("height", SLIDE_H_IN))
        x, y, w, h = scale_box(enriched, units, source.size)
        if box.get("source_bbox_px"):
            sx, sy, sw, sh = [int(v) for v in box["source_bbox_px"]]
            draw.rectangle((sx, sy, sx + sw, sy + sh), outline="#00A36C", width=2)
        if mode in {"boxes", "faded"}:
            draw.rectangle((x, y, x + w, y + h), outline="#006BFF", width=2)
            label = f"{idx} {box.get('role', '')}".strip()
            draw.text((x + 2, max(0, y - 16)), label, fill="#006BFF", font=ImageFont.load_default())
        if mode in {"faded", "text-only"}:
            draw_text_box(draw, enriched, (x, y, w, h), source.size[0])
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="Render manifest alignment previews.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--prefix", default="alignment")
    parser.add_argument("--modes", nargs="+", default=list(DEFAULT_MODES), choices=list(DEFAULT_MODES))
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    slide = manifest["slides"][0]
    source_path = resolve_source(args.manifest, manifest, slide, args.source)
    source = Image.open(source_path).convert("RGB")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for mode in args.modes:
        preview = draw_preview(source, manifest, slide, mode)
        preview.save(args.out_dir / f"{args.prefix}-{mode}.png")
        print(args.out_dir / f"{args.prefix}-{mode}.png")


if __name__ == "__main__":
    main()
