#!/usr/bin/env python3
"""Render manifest-first editable-text previews and simple QA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
OUT_W = 1920
OUT_H = 1080

ROLE_COLORS = {
    "title": (32, 86, 210, 42),
    "subtitle": (32, 86, 210, 28),
    "section": (220, 46, 46, 36),
    "gate-label": (220, 46, 46, 28),
    "evidence-header": (220, 46, 46, 28),
    "evidence-body": (60, 60, 60, 24),
    "panel-title": (220, 46, 46, 34),
    "panel-copy": (60, 60, 60, 24),
    "line-item": (60, 60, 60, 24),
    "takeaway": (220, 46, 46, 38),
    "source": (80, 80, 80, 18),
}


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def px_box(box: dict[str, Any], slide_w: float, slide_h: float, image_w: int, image_h: int) -> tuple[int, int, int, int]:
    x = int(round(float(box["x"]) / slide_w * image_w))
    y = int(round(float(box["y"]) / slide_h * image_h))
    w = int(round(float(box["w"]) / slide_w * image_w))
    h = int(round(float(box["h"]) / slide_h * image_h))
    return x, y, w, h


def font_path(box: dict[str, Any]) -> str | None:
    bold = bool(box.get("bold", False))
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def load_font(box: dict[str, Any], image_w: int, slide_w: float) -> ImageFont.ImageFont:
    size_pt = float(box.get("font_size", 12))
    px_size = max(6, int(round(size_pt * image_w / slide_w / 72)))
    path = font_path(box)
    if path:
        return ImageFont.truetype(path, px_size)
    return ImageFont.load_default()


def rgb(raw: str | None, default: tuple[int, int, int]) -> tuple[int, int, int]:
    if not raw:
        return default
    raw = raw.strip().lstrip("#")
    if len(raw) != 6:
        return default
    return tuple(int(raw[i : i + 2], 16) for i in (0, 2, 4))


def line_metrics(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return left, top, right, bottom


def draw_text_box(draw: ImageDraw.ImageDraw, box: dict[str, Any], slide_w: float, slide_h: float, image_w: int, image_h: int) -> dict[str, Any]:
    x, y, w, h = px_box(box, slide_w, slide_h, image_w, image_h)
    margin_pt = float(box.get("margin", 0))
    margin_px = int(round(margin_pt * image_w / slide_w / 72))
    font = load_font(box, image_w, slide_w)
    color = rgb(box.get("color"), (25, 25, 25))
    tracking = float(box.get("character_spacing", 0.0)) * image_w / slide_w / 72
    line_spacing = float(box.get("line_spacing", 1.1))
    lines = str(box.get("text", "")).splitlines() or [""]
    cursor_y = y + margin_px
    max_right = x + margin_px
    max_bottom = cursor_y
    for line in lines:
        left, top, right, bottom = line_metrics(draw, line, font)
        line_w = (right - left) + max(0, len(line) - 1) * tracking
        align = str(box.get("align", "left")).lower()
        cursor_x = x + margin_px
        if align == "center":
            cursor_x = x + (w - line_w) / 2
        elif align == "right":
            cursor_x = x + w - margin_px - line_w
        char_x = cursor_x - left
        for char in line:
            draw.text((char_x, cursor_y - top), char, font=font, fill=color)
            c_left, _, c_right, _ = line_metrics(draw, char, font)
            char_x += (c_right - c_left) + tracking
        max_right = max(max_right, int(round(cursor_x + line_w)))
        max_bottom = max(max_bottom, int(round(cursor_y + (bottom - top))))
        cursor_y += int(round((bottom - top) * line_spacing))
    overflow = max_right > x + w - margin_px + 1 or max_bottom > y + h - margin_px + 1
    return {
        "name": box.get("name", ""),
        "role": box.get("role", ""),
        "box_px": [x, y, w, h],
        "rendered_px": [x + margin_px, y + margin_px, max_right - x - margin_px, max_bottom - y - margin_px],
        "overflow": overflow,
    }


def draw_safe_zones(base: Image.Image, manifest: dict[str, Any], debug_labels: bool) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    slide = manifest["slides"][0]
    slide_size = manifest.get("slide_size") or {}
    slide_w = float(slide_size.get("width", SLIDE_W_IN))
    slide_h = float(slide_size.get("height", SLIDE_H_IN))
    label_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14) if Path("C:/Windows/Fonts/arial.ttf").exists() else ImageFont.load_default()
    for idx, box in enumerate(slide.get("text_boxes", []), start=1):
        x, y, w, h = px_box(box, slide_w, slide_h, base.width, base.height)
        role = str(box.get("role", "text"))
        fill = ROLE_COLORS.get(role, (32, 86, 210, 24))
        outline = fill[:3] + (160,)
        draw.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=2)
        if debug_labels:
            draw.text((x + 4, y + 3), f"{idx} {role}", font=label_font, fill=(30, 86, 210, 230))


def render(manifest_path: Path, out_dir: Path, background: Path | None) -> None:
    manifest = load_manifest(manifest_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    slide = manifest["slides"][0]
    slide_size = manifest.get("slide_size") or {}
    slide_w = float(slide_size.get("width", SLIDE_W_IN))
    slide_h = float(slide_size.get("height", SLIDE_H_IN))

    safe = Image.new("RGB", (OUT_W, OUT_H), "white")
    draw_safe_zones(safe, manifest, True)
    safe.save(out_dir / "safe_zone_map.png")

    clean_safe = Image.new("RGB", (OUT_W, OUT_H), "white")
    draw_safe_zones(clean_safe, manifest, False)
    clean_safe.save(out_dir / "safe_zone_reference_clean.png")

    text_only = Image.new("RGB", (OUT_W, OUT_H), "white")
    draw_safe_zones(text_only, manifest, False)
    text_draw = ImageDraw.Draw(text_only)
    qa_items = []
    for box in slide.get("text_boxes", []):
        qa_items.append(draw_text_box(text_draw, box, slide_w, slide_h, OUT_W, OUT_H))
    text_only.save(out_dir / "manifest_preview_text_only.png")

    if background:
        bg = Image.open(background).convert("RGB").resize((OUT_W, OUT_H))
    else:
        bg = Image.new("RGB", (OUT_W, OUT_H), (248, 248, 246))
    composite = bg.copy()
    comp_draw = ImageDraw.Draw(composite)
    qa_items = []
    for box in slide.get("text_boxes", []):
        qa_items.append(draw_text_box(comp_draw, box, slide_w, slide_h, OUT_W, OUT_H))
    composite.save(out_dir / "composite_preview.png")

    debug = bg.copy()
    draw_safe_zones(debug, manifest, True)
    debug_draw = ImageDraw.Draw(debug)
    for box in slide.get("text_boxes", []):
        draw_text_box(debug_draw, box, slide_w, slide_h, OUT_W, OUT_H)
    debug.save(out_dir / "composite_debug_zones.png")

    qa = {
        "manifest": str(manifest_path),
        "background": str(background) if background else None,
        "image_size": [OUT_W, OUT_H],
        "text_boxes": len(slide.get("text_boxes", [])),
        "overflow_count": sum(1 for item in qa_items if item["overflow"]),
        "items": qa_items,
    }
    (out_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out_dir / "safe_zone_map.png")
    print(out_dir / "safe_zone_reference_clean.png")
    print(out_dir / "manifest_preview_text_only.png")
    print(out_dir / "composite_preview.png")
    print(out_dir / "composite_debug_zones.png")
    print(out_dir / "qa_report.json")
    print(json.dumps({"text_boxes": qa["text_boxes"], "overflow_count": qa["overflow_count"]}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render manifest-first editable-text previews.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--background", type=Path)
    args = parser.parse_args()
    render(args.manifest, args.out_dir, args.background)


if __name__ == "__main__":
    main()
