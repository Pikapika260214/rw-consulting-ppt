#!/usr/bin/env python3
"""Refine source_bbox_px values by detecting text ink inside existing bboxes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5

RED_ROLES = {"section", "evidence-header", "panel-title", "takeaway"}
SKIP_ROLES = {"gate-number"}


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
    return r > 120 and g < 95 and b < 95 and r > g * 1.35 and r > b * 1.35


def is_dark(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return max(r, g, b) < 150 and min(r, g, b) < 125


def ink_bbox(crop: Image.Image, role: str) -> tuple[int, int, int, int] | None:
    pixels = crop.convert("RGB")
    width, height = pixels.size
    points: list[tuple[int, int]] = []
    red_role = role in RED_ROLES
    for y in range(height):
        for x in range(width):
            pixel = pixels.getpixel((x, y))
            if (red_role and is_red(pixel)) or (not red_role and is_dark(pixel)):
                points.append((x, y))
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def clamp_bbox(x: int, y: int, w: int, h: int, image_w: int, image_h: int) -> list[int]:
    x = max(0, min(x, image_w - 1))
    y = max(0, min(y, image_h - 1))
    w = max(1, min(w, image_w - x))
    h = max(1, min(h, image_h - y))
    return [x, y, w, h]


def main() -> None:
    parser = argparse.ArgumentParser(description="Refine manifest source bboxes by text ink detection.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pad-x", type=int, default=2)
    parser.add_argument("--pad-y", type=int, default=1)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    slide_w = float((manifest.get("slide_size") or {}).get("width", SLIDE_W_IN))
    slide_h = float((manifest.get("slide_size") or {}).get("height", SLIDE_H_IN))
    slide = manifest["slides"][0]
    source_path = resolve_source(args.manifest, manifest, slide, args.source)
    image = Image.open(source_path).convert("RGB")
    image_w, image_h = image.size

    refined = 0
    skipped = 0
    for box in slide.get("text_boxes", []):
        role = str(box.get("role", ""))
        bbox = box.get("source_bbox_px")
        if not bbox or role in SKIP_ROLES:
            skipped += 1
            continue
        x, y, w, h = [int(v) for v in bbox]
        crop = image.crop((x, y, x + w, y + h))
        local = ink_bbox(crop, role)
        if not local:
            skipped += 1
            continue
        lx1, ly1, lx2, ly2 = local
        nx = x + lx1 - args.pad_x
        ny = y + ly1 - args.pad_y
        nw = (lx2 - lx1) + args.pad_x * 2
        nh = (ly2 - ly1) + args.pad_y * 2
        new_bbox = clamp_bbox(nx, ny, nw, nh, image_w, image_h)
        box["source_bbox_px"] = new_bbox
        box["x"] = round(new_bbox[0] / image_w * slide_w, 3)
        box["y"] = round(new_bbox[1] / image_h * slide_h, 3)
        box["w"] = round(new_bbox[2] / image_w * slide_w, 3)
        box["h"] = round(new_bbox[3] / image_h * slide_h, 3)
        box["render_anchor"] = "glyph_bbox"
        box["alignment_status"] = "ink-bbox"
        refined += 1

    manifest["phase"] = "ppt-to-editable-ink-bbox-refinement"
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + f" Round 6 refines source bboxes from detected ink regions. refined={refined}, skipped={skipped}."
    ).strip()
    manifest["ink_bbox_refinement"] = {"refined": refined, "skipped": skipped, "pad_x": args.pad_x, "pad_y": args.pad_y}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(f"refined={refined} skipped={skipped}")


if __name__ == "__main__":
    main()
