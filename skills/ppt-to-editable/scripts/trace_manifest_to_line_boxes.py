#!/usr/bin/env python3
"""Convert block-level manifest text boxes into line-level trace boxes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5

RED_ROLES = {"section", "evidence-header", "panel-title", "takeaway"}
WHITE_ROLES = {"gate-number"}


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


def is_red(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return r > 120 and g < 105 and b < 105 and r > g * 1.25 and r > b * 1.25


def is_dark(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return max(r, g, b) < 155 and min(r, g, b) < 135


def is_white(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return r > 205 and g > 205 and b > 205


def pixel_matches(pixel: tuple[int, int, int], role: str) -> bool:
    if role in RED_ROLES:
        return is_red(pixel)
    if role in WHITE_ROLES:
        return is_white(pixel)
    return is_dark(pixel)


def clamp_bbox(x: int, y: int, w: int, h: int, image_w: int, image_h: int) -> list[int]:
    x = max(0, min(x, image_w - 1))
    y = max(0, min(y, image_h - 1))
    w = max(1, min(w, image_w - x))
    h = max(1, min(h, image_h - y))
    return [x, y, w, h]


def row_bands(crop: Image.Image, role: str, max_gap: int = 2) -> list[tuple[int, int]]:
    pixels = crop.convert("RGB")
    width, height = pixels.size
    counts = []
    for y in range(height):
        count = 0
        for x in range(width):
            if pixel_matches(pixels.getpixel((x, y)), role):
                count += 1
        counts.append(count)
    threshold = max(2, int(width * 0.015))
    active = [idx for idx, count in enumerate(counts) if count >= threshold]
    if not active:
        return []
    bands: list[tuple[int, int]] = []
    start = prev = active[0]
    for y in active[1:]:
        if y - prev <= max_gap + 1:
            prev = y
            continue
        bands.append((start, prev + 1))
        start = prev = y
    bands.append((start, prev + 1))
    return bands


def ink_bbox_for_band(crop: Image.Image, role: str, y1: int, y2: int, pad_x: int, pad_y: int) -> list[int] | None:
    pixels = crop.convert("RGB")
    width, height = pixels.size
    points: list[tuple[int, int]] = []
    for y in range(max(0, y1), min(height, y2)):
        for x in range(width):
            if pixel_matches(pixels.getpixel((x, y)), role):
                points.append((x, y))
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x1 = max(0, min(xs) - pad_x)
    x2 = min(width, max(xs) + 1 + pad_x)
    yy1 = max(0, min(ys) - pad_y)
    yy2 = min(height, max(ys) + 1 + pad_y)
    return [x1, yy1, x2 - x1, yy2 - yy1]


def split_evenly(bbox: list[int], count: int) -> list[list[int]]:
    x, y, w, h = [int(v) for v in bbox]
    if count <= 1:
        return [[x, y, w, h]]
    line_h = h / count
    result = []
    for idx in range(count):
        ly = int(round(y + idx * line_h))
        next_y = int(round(y + (idx + 1) * line_h))
        result.append([x, ly, w, max(1, next_y - ly)])
    return result


def line_bboxes(image: Image.Image, box: dict[str, Any], line_count: int, pad_x: int, pad_y: int) -> tuple[list[list[int]], str]:
    bbox = box.get("source_bbox_px")
    if not bbox:
        return [], "missing-source-bbox"
    image_w, image_h = image.size
    x, y, w, h = [int(v) for v in bbox]
    crop = image.crop((x, y, x + w, y + h))
    role = str(box.get("role", ""))
    bands = row_bands(crop, role)
    local_boxes: list[list[int]] = []
    for band in bands:
        local = ink_bbox_for_band(crop, role, band[0], band[1], pad_x, pad_y)
        if local:
            local_boxes.append(local)
    if len(local_boxes) == line_count:
        result = [
            clamp_bbox(x + lx, y + ly, lw, lh, image_w, image_h)
            for lx, ly, lw, lh in local_boxes
        ]
        return result, "ink-lines"
    return split_evenly([x, y, w, h], line_count), f"even-split-from-{len(local_boxes)}-ink-lines"


def px_to_in_bbox(bbox: list[int], image_size: tuple[int, int], slide_w: float, slide_h: float) -> dict[str, float]:
    image_w, image_h = image_size
    x, y, w, h = bbox
    return {
        "x": round(x / image_w * slide_w, 3),
        "y": round(y / image_h * slide_h, 3),
        "w": round(w / image_w * slide_w, 3),
        "h": round(h / image_h * slide_h, 3),
    }


def trace_box(box: dict[str, Any], image: Image.Image, slide_w: float, slide_h: float, pad_x: int, pad_y: int) -> list[dict[str, Any]]:
    text = str(box.get("text", ""))
    lines = text.splitlines() or [text]
    source_boxes, method = line_bboxes(image, box, len(lines), pad_x, pad_y)
    if not source_boxes:
        source_boxes = [box.get("source_bbox_px") or [0, 0, 1, 1]]
        method = "fallback-original-box"
    output: list[dict[str, Any]] = []
    for idx, (line, bbox) in enumerate(zip(lines, source_boxes), start=1):
        next_box = dict(box)
        next_box["text"] = line
        next_box["name"] = f"{box.get('name') or box.get('role') or 'Text'} line {idx}"
        next_box["parent_name"] = box.get("name") or box.get("role")
        next_box["line_index"] = idx
        next_box["line_count"] = len(lines)
        next_box["trace_level"] = "line"
        next_box["line_trace_method"] = method
        next_box["source_bbox_px"] = bbox
        next_box.update(px_to_in_bbox(bbox, image.size, slide_w, slide_h))
        next_box["align"] = "left"
        next_box["line_spacing"] = 1.0
        next_box["render_anchor"] = "glyph_bbox"
        next_box["no_wrap"] = True
        next_box["alignment_status"] = "line-trace"
        output.append(next_box)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert block-level manifest text boxes to line-level trace boxes.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pad-x", type=int, default=2)
    parser.add_argument("--pad-y", type=int, default=1)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    slide_size = manifest.get("slide_size") or {}
    slide_w = float(slide_size.get("width", SLIDE_W_IN))
    slide_h = float(slide_size.get("height", SLIDE_H_IN))
    slide = manifest["slides"][0]
    source_path = resolve_source(args.manifest, manifest, slide, args.source)
    image = Image.open(source_path).convert("RGB")

    old_boxes = slide.get("text_boxes", [])
    new_boxes: list[dict[str, Any]] = []
    for box in old_boxes:
        new_boxes.extend(trace_box(box, image, slide_w, slide_h, args.pad_x, args.pad_y))
    slide["text_boxes"] = new_boxes
    manifest["phase"] = "ppt-to-editable-line-trace"
    manifest["trace_level"] = "line"
    manifest["line_trace_summary"] = {"source_boxes": len(old_boxes), "line_boxes": len(new_boxes)}
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + f" Line trace converts {len(old_boxes)} source boxes into {len(new_boxes)} editable line boxes."
    ).strip()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(f"source_boxes={len(old_boxes)} line_boxes={len(new_boxes)}")


if __name__ == "__main__":
    main()
