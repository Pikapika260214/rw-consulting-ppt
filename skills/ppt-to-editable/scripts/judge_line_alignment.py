#!/usr/bin/env python3
"""Judge line-level manifest alignment and emit patch recommendations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
TRACKING_CAPS = {
    "title": 0.14,
    "subtitle": 0.12,
    "section": 0.14,
    "gate-number": 0.0,
    "gate-label": 0.08,
    "evidence-header": 0.08,
    "evidence-body": 0.12,
    "panel-title": 0.12,
    "panel-copy": 0.12,
    "line-item": 0.12,
    "takeaway": 0.14,
    "source": 0.06,
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


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return left, top, right, bottom


def tracking_px(box: dict[str, Any], image_width: int, slide_w: float) -> float:
    return float(box.get("character_spacing", 0.0)) * image_width / slide_w / 72


def box_to_px(box: dict[str, Any], image_size: tuple[int, int], slide_w: float, slide_h: float) -> list[float]:
    image_w, image_h = image_size
    return [
        float(box["x"]) / slide_w * image_w,
        float(box["y"]) / slide_h * image_h,
        float(box["w"]) / slide_w * image_w,
        float(box["h"]) / slide_h * image_h,
    ]


def rendered_bbox(draw: ImageDraw.ImageDraw, box: dict[str, Any], image_size: tuple[int, int], slide_w: float, slide_h: float) -> list[float]:
    x, y, w, _ = box_to_px(box, image_size, slide_w, slide_h)
    font = font_at_size(float(box.get("font_size", 12)), image_size[0], slide_w, bool(box.get("bold", False)))
    text = str(box.get("text", ""))
    left, top, right, bottom = text_bbox(draw, text, font)
    text_w = right - left + max(0, len(text) - 1) * tracking_px(box, image_size[0], slide_w)
    align = str(box.get("align", "left")).lower()
    anchor = str(box.get("render_anchor", "box_frame")).lower()
    shift_x, shift_y = box.get("text_shift_px", [0, 0])
    lx = x
    if align == "center":
        lx = x + (w - text_w) / 2
    elif align == "right":
        lx = x + w - text_w
    ly = y
    if anchor == "glyph_bbox":
        lx -= left
        ly -= top
    return [lx + left + float(shift_x), ly + top + float(shift_y), text_w, bottom - top]


def classify(metrics: dict[str, float]) -> list[str]:
    labels: list[str] = []
    if metrics["dx"] > 4:
        labels.append("box_shift_right")
    elif metrics["dx"] < -4:
        labels.append("box_shift_left")
    if metrics["dy"] > 4:
        labels.append("box_shift_down")
    elif metrics["dy"] < -4:
        labels.append("box_shift_up")
    if metrics["width_ratio"] < 0.90:
        labels.append("font_too_small_or_narrow")
    elif metrics["width_ratio"] > 1.10:
        labels.append("font_too_large_or_wide")
    if metrics["height_ratio"] < 0.82:
        labels.append("font_height_too_small")
    elif metrics["height_ratio"] > 1.18:
        labels.append("font_height_too_large")
    return labels or ["ok"]


def patch_for(metrics: dict[str, float], box: dict[str, Any], slide_w: float, slide_h: float, image_size: tuple[int, int]) -> dict[str, Any]:
    image_w, image_h = image_size
    dx_in = -metrics["dx"] / image_w * slide_w
    dy_in = -metrics["dy"] / image_h * slide_h
    font_scale = 1.0
    height_out_of_tolerance = metrics["height_ratio"] < 0.90 or metrics["height_ratio"] > 1.10
    width_out_of_tolerance = metrics["width_ratio"] < 0.92 or metrics["width_ratio"] > 1.08
    if height_out_of_tolerance and metrics["height_ratio"] > 0:
        font_scale = 1.0 / metrics["height_ratio"]
    font_scale = max(0.92, min(1.08, font_scale))
    current_spacing = float(box.get("character_spacing", 0.0))
    tracking_delta = 0.0
    role = str(box.get("role", ""))
    cap = TRACKING_CAPS.get(role, 0.10)
    if width_out_of_tolerance and not height_out_of_tolerance and cap > 0 and metrics["width_ratio"] > 0:
        current_width = metrics["rendered_width_px"]
        target_width = metrics["source_width_px"]
        char_slots = max(1, len(str(box.get("text", ""))) - 1)
        tracking_delta_px = (target_width - current_width) / char_slots
        tracking_delta = tracking_delta_px / image_w * slide_w * 72
        tracking_delta = max(-cap, min(cap, tracking_delta))
    patch: dict[str, Any] = {
        "name": box.get("name"),
        "x_delta": round(dx_in, 4) if abs(metrics["dx"]) > 4 else 0,
        "y_delta": round(dy_in, 4) if abs(metrics["dy"]) > 4 else 0,
        "font_size_multiplier": round(font_scale, 4) if abs(font_scale - 1.0) > 0.035 else 1.0,
        "character_spacing_delta": round(tracking_delta, 4) if abs(tracking_delta) > 0.03 else 0,
        "patch_policy": "staged-position-font-then-tracking",
    }
    if patch["font_size_multiplier"] != 1.0:
        patch["font_size_next"] = round(float(box.get("font_size", 12)) * patch["font_size_multiplier"], 1)
    if patch["character_spacing_delta"]:
        patch["character_spacing_next"] = round(current_spacing + patch["character_spacing_delta"], 3)
    return patch


def judge(manifest_path: Path, source_override: Path | None) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    slide = manifest["slides"][0]
    source_path = resolve_source(manifest_path, manifest, slide, source_override)
    source = Image.open(source_path).convert("RGB")
    draw = ImageDraw.Draw(source)
    slide_size = manifest.get("slide_size") or {}
    slide_w = float(slide_size.get("width", SLIDE_W_IN))
    slide_h = float(slide_size.get("height", SLIDE_H_IN))
    details: list[dict[str, Any]] = []
    for idx, box in enumerate(slide.get("text_boxes", []), start=1):
        source_bbox = box.get("source_bbox_px")
        if not source_bbox:
            continue
        sx, sy, sw, sh = [float(v) for v in source_bbox]
        rx, ry, rw, rh = rendered_bbox(draw, box, source.size, slide_w, slide_h)
        metrics = {
            "dx": round(rx - sx, 2),
            "dy": round(ry - sy, 2),
            "width_ratio": round(rw / sw, 3) if sw else 0,
            "height_ratio": round(rh / sh, 3) if sh else 0,
            "rendered_width_px": round(rw, 2),
            "source_width_px": round(sw, 2),
            "rendered_height_px": round(rh, 2),
            "source_height_px": round(sh, 2),
        }
        labels = classify(metrics)
        details.append({
            "index": idx,
            "name": box.get("name"),
            "role": box.get("role"),
            "text": box.get("text"),
            "source_bbox_px": [round(v, 2) for v in [sx, sy, sw, sh]],
            "rendered_bbox_px": [round(v, 2) for v in [rx, ry, rw, rh]],
            "metrics": metrics,
            "failure_labels": labels,
            "patch": patch_for(metrics, box, slide_w, slide_h, source.size),
        })
    failing = [d for d in details if d["failure_labels"] != ["ok"]]
    label_counts: dict[str, int] = {}
    for item in details:
        for label in item["failure_labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1
    return {
        "source": str(source_path),
        "summary": {
            "line_boxes": len(details),
            "failing_boxes": len(failing),
            "ok_boxes": len(details) - len(failing),
            "label_counts": label_counts,
        },
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge line-level manifest alignment.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = judge(args.manifest, args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
