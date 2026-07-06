#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def resolve_cli_path(value: str) -> Path:
    return Path(value).resolve()


def clamp(value: float, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, int(round(value))))


def as_box(values: list[Any]) -> tuple[int, int, int, int]:
    if len(values) != 4:
        raise ValueError(f"bbox must have four values, got {values!r}")
    x1, y1, x2, y2 = (int(round(float(v))) for v in values)
    return x1, y1, x2, y2


def box_from_spec(spec: dict[str, Any]) -> tuple[int, int, int, int]:
    if "bbox" in spec:
        return as_box(spec["bbox"])
    if "center" in spec and "size" in spec:
        cx, cy = (float(v) for v in spec["center"])
        size = spec["size"]
        if isinstance(size, list):
            if len(size) != 2:
                raise ValueError(f"size list must have two values for {spec.get('id')}")
            w, h = float(size[0]), float(size[1])
        else:
            w = h = float(size)
        return (
            int(round(cx - w / 2)),
            int(round(cy - h / 2)),
            int(round(cx + w / 2)),
            int(round(cy + h / 2)),
        )
    raise ValueError(f"badge {spec.get('id', '<unknown>')} needs bbox or center+size")


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[tuple[int, int, int, int], bool]:
    x1, y1, x2, y2 = box
    clamped = (max(0, x1), max(0, y1), min(width, x2), min(height, y2))
    return clamped, clamped != box


def is_red_ink(r: int, g: int, b: int) -> bool:
    return r > 110 and r - max(g, b) > 35


def is_dark_ink(r: int, g: int, b: int) -> bool:
    return max(r, g, b) < 135


def is_core_ink(r: int, g: int, b: int, ink_mode: str) -> bool:
    if ink_mode == "red":
        return is_red_ink(r, g, b)
    if ink_mode == "dark":
        return is_dark_ink(r, g, b)
    return is_red_ink(r, g, b) or is_dark_ink(r, g, b)


def largest_component(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    remaining = set(points)
    best: list[tuple[int, int]] = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = [start]
        while stack:
            x, y = stack.pop()
            for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)
        if len(component) > len(best):
            best = component
    return best


def find_ink_bbox(
    image: Image.Image,
    *,
    ink_mode: str,
    largest_only: bool,
) -> tuple[int, int, int, int]:
    pts: list[tuple[int, int]] = []
    rgb = image.convert("RGB")
    for y in range(rgb.height):
        for x in range(rgb.width):
            if is_core_ink(*rgb.getpixel((x, y)), ink_mode):
                pts.append((x, y))
    if not pts:
        raise ValueError("No source icon ink detected")
    if largest_only:
        pts = largest_component(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def expand_box(box: tuple[int, int, int, int], pad: int, limit_w: int, limit_h: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return max(0, x1 - pad), max(0, y1 - pad), min(limit_w, x2 + pad), min(limit_h, y2 + pad)


def edge_has_core_ink(image: Image.Image, ink_mode: str) -> bool:
    rgb = image.convert("RGB")
    for x in range(rgb.width):
        if is_core_ink(*rgb.getpixel((x, 0)), ink_mode):
            return True
        if is_core_ink(*rgb.getpixel((x, rgb.height - 1)), ink_mode):
            return True
    for y in range(rgb.height):
        if is_core_ink(*rgb.getpixel((0, y)), ink_mode):
            return True
        if is_core_ink(*rgb.getpixel((rgb.width - 1, y)), ink_mode):
            return True
    return False


def glyph_alpha(crop: Image.Image, ink_mode: str) -> Image.Image:
    rgba = crop.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, _a = pixels[x, y]
            max_c = max(r, g, b)
            red_strength = r - max(g, b)
            red_ink = r > 95 and red_strength > 18
            dark_ink = max_c < 232
            if ink_mode == "red":
                alpha = clamp((red_strength - 12) * 6.5) if red_ink else 0
            elif red_ink:
                alpha = clamp((red_strength - 12) * 6.5)
            elif dark_ink:
                alpha = clamp((232 - max_c) * 3.0)
            else:
                alpha = 0
            pixels[x, y] = (r, g, b, alpha)
    return rgba


def draw_badge_base(size: int, spec: dict[str, Any]) -> Image.Image:
    scale = 4
    big_size = size * scale
    base = Image.new("RGBA", (big_size, big_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    base_spec = spec.get("base", {})
    fill = tuple(base_spec.get("fill_rgba", [255, 255, 255, 255]))
    stroke = tuple(base_spec.get("stroke_rgba", [207, 211, 216, 255]))
    stroke_width = int(base_spec.get("stroke_width_px", 1)) * scale
    inset = base_spec.get("ellipse_inset_px", [6, 5, 7, 8])
    if isinstance(inset, (int, float)):
        left = top = right = bottom = float(inset)
    else:
        left, top, right, bottom = (float(v) for v in inset)
    ellipse = (
        left * scale,
        top * scale,
        (size - right) * scale,
        (size - bottom) * scale,
    )
    draw.ellipse(ellipse, fill=fill, outline=stroke, width=max(stroke_width, 1))
    return base.resize((size, size), Image.Resampling.LANCZOS)


def resize_fit(image: Image.Image, max_size: int) -> Image.Image:
    scale = min(max_size / image.width, max_size / image.height)
    w = max(1, int(round(image.width * scale)))
    h = max(1, int(round(image.height * scale)))
    return image.resize((w, h), Image.Resampling.LANCZOS)


def make_debug_sheet(records: list[dict[str, Any]], out_path: Path) -> None:
    if not records:
        return
    cell_w, cell_h = 170, 142
    cols = int(records[0].get("debug_cols", 5)) if records else 5
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, rec in enumerate(records):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        crop = Image.open(rec["output_path"]).convert("RGBA")
        preview = Image.new("RGBA", crop.size, (255, 255, 255, 255))
        preview.alpha_composite(crop)
        sheet.paste(preview.convert("RGB"), (x + 24, y + 8))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(220, 220, 220))
        draw.text((x + 6, y + 102), str(rec["id"])[:24], fill=(0, 0, 0))
        draw.text((x + 6, y + 120), f"{rec['glyph_width']}x{rec['glyph_height']} glyph", fill=(90, 90, 90))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def make_badge(source: Image.Image, spec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    badge_id = str(spec["id"])
    requested_box = box_from_spec(spec)
    full_box, clipped = clamp_box(requested_box, source.width, source.height)
    if full_box[2] <= full_box[0] or full_box[3] <= full_box[1]:
        raise ValueError(f"badge {badge_id} has empty bbox after clipping: {full_box}")

    ink_mode = str(spec.get("ink_mode", "auto")).lower()
    largest_only = bool(spec.get("largest_component", ink_mode == "red"))
    full_crop = source.crop(full_box)
    ink_bbox_local = find_ink_bbox(full_crop, ink_mode=ink_mode, largest_only=largest_only)
    padding = int(round(float(spec.get("glyph_padding", spec.get("padding", 6)))))
    glyph_box_local = expand_box(ink_bbox_local, padding, full_crop.width, full_crop.height)
    fx1, fy1, _fx2, _fy2 = full_box
    gx1, gy1, gx2, gy2 = glyph_box_local
    source_glyph_box = (fx1 + gx1, fy1 + gy1, fx1 + gx2, fy1 + gy2)
    source_glyph = source.crop(source_glyph_box)
    glyph = glyph_alpha(source_glyph, ink_mode)
    target_max = int(round(float(spec["target_max"])))
    glyph = resize_fit(glyph, target_max)

    output_size = int(round(float(spec.get("output_size", spec.get("badge_size", full_box[2] - full_box[0])))))
    badge = draw_badge_base(output_size, spec)
    x = int(round((output_size - glyph.width) / 2 + float(spec.get("dx", 0))))
    y = int(round((output_size - glyph.height) / 2 + float(spec.get("dy", 0))))
    badge.alpha_composite(glyph, (x, y))

    output_name = str(spec.get("output_name", f"{badge_id}.png"))
    out_path = out_dir / output_name
    badge.save(out_path)

    warnings: list[str] = []
    if clipped:
        warnings.append("badge_bbox_clipped_to_source")
    if edge_has_core_ink(source_glyph, ink_mode):
        warnings.append("glyph_ink_touches_crop_edge")

    return {
        "id": badge_id,
        "plan_element_id": spec.get("plan_element_id"),
        "output_path": str(out_path.resolve()),
        "requested_badge_crop_px": list(requested_box),
        "full_badge_crop_px": list(full_box),
        "detected_ink_bbox_px": [
            fx1 + ink_bbox_local[0],
            fy1 + ink_bbox_local[1],
            fx1 + ink_bbox_local[2],
            fy1 + ink_bbox_local[3],
        ],
        "source_crop_px": list(source_glyph_box),
        "source_glyph_crop_px": list(source_glyph_box),
        "width": badge.width,
        "height": badge.height,
        "glyph_width": glyph.width,
        "glyph_height": glyph.height,
        "ink_mode": ink_mode,
        "largest_component": largest_only,
        "warnings": warnings,
    }


def compose_badges(
    manifest_path: Path,
    out_dir_arg: str | None,
    report_arg: str | None,
    debug_arg: str | None,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    base = manifest_path.parent
    source_path = resolve_path(manifest["source_image"], base)
    source = Image.open(source_path).convert("RGB")

    if out_dir_arg:
        out_dir = resolve_cli_path(out_dir_arg)
    else:
        out_dir = resolve_path(manifest.get("output_dir", "badge-composites"), base)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "tool": "make_clean_badge_composites.py",
        "manifest": str(manifest_path.resolve()),
        "source_image": str(source_path),
        "source_size_px": [source.width, source.height],
        "out_dir": str(out_dir),
        "outputs": [],
        "warnings": [],
    }

    for spec in manifest.get("badges", manifest.get("crops", [])):
        record = make_badge(source, spec, out_dir)
        report["outputs"].append(record)
        for warning in record["warnings"]:
            report["warnings"].append({"id": record["id"], "warning": warning})

    if debug_arg:
        debug_path = resolve_cli_path(debug_arg)
    elif manifest.get("debug_sheet"):
        debug_path = resolve_path(manifest["debug_sheet"], base)
    else:
        debug_path = out_dir / "badge_composite_debug_sheet.png"
    make_debug_sheet(report["outputs"], debug_path)
    report["debug_sheet"] = str(debug_path.resolve())

    if report_arg:
        report_path = resolve_cli_path(report_arg)
    elif manifest.get("report"):
        report_path = resolve_path(manifest["report"], base)
    else:
        report_path = out_dir / "badge_composite_report.json"
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Create clean circular badge composites from source icon glyphs.")
    parser.add_argument("manifest", help="Path to clean badge composite manifest JSON.")
    parser.add_argument("--out-dir", help="Output directory for badge PNGs.")
    parser.add_argument("--report", help="Path to badge composite report JSON.")
    parser.add_argument("--debug", help="Path to debug sheet PNG.")
    args = parser.parse_args()
    report = compose_badges(Path(args.manifest).resolve(), args.out_dir, args.report, args.debug)
    print(json.dumps({"outputs": len(report["outputs"]), "warnings": len(report["warnings"]), "debug_sheet": report["debug_sheet"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
