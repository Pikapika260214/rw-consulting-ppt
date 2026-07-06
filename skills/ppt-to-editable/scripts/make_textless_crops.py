#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any

from PIL import Image, ImageDraw, ImageFilter


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


def as_box(values: list[Any]) -> tuple[int, int, int, int]:
    if len(values) != 4:
        raise ValueError(f"bbox must have four values, got {values!r}")
    x1, y1, x2, y2 = (int(round(float(v))) for v in values)
    return x1, y1, x2, y2


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[tuple[int, int, int, int], bool]:
    x1, y1, x2, y2 = box
    clamped = (max(0, x1), max(0, y1), min(width, x2), min(height, y2))
    return clamped, clamped != box


def ocr_record_box(record: dict[str, Any]) -> tuple[int, int, int, int]:
    if "source_bbox_px" in record:
        return as_box(record["source_bbox_px"])
    if "bbox_px" in record:
        x, y, w, h = (float(value) for value in record["bbox_px"])
        return int(round(x)), int(round(y)), int(round(x + w)), int(round(y + h))
    raise ValueError(f"OCR record lacks bbox_px/source_bbox_px: {record.get('id')}")


def box_area(box: tuple[int, int, int, int]) -> int:
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return box_area((x1, y1, x2, y2))


def normalize_rel_box(
    mask_spec: Any,
    crop_box: tuple[int, int, int, int],
    crop_size: tuple[int, int],
    default_padding: int,
) -> tuple[int, int, int, int]:
    relative = False
    if isinstance(mask_spec, dict):
        box = as_box(mask_spec["bbox"])
        relative = bool(mask_spec.get("relative")) or str(mask_spec.get("coordinate_space", "")).lower() == "crop"
        padding = int(mask_spec.get("padding", default_padding))
    else:
        box = as_box(mask_spec)
        padding = default_padding

    if relative:
        rel = box
    else:
        crop_x1, crop_y1, _crop_x2, _crop_y2 = crop_box
        rel = (box[0] - crop_x1, box[1] - crop_y1, box[2] - crop_x1, box[3] - crop_y1)

    x1, y1, x2, y2 = rel
    rel = (x1 - padding, y1 - padding, x2 + padding, y2 + padding)
    clamped, _ = clamp_box(rel, crop_size[0], crop_size[1])
    return clamped


def ocr_mode_enabled(spec: dict[str, Any]) -> bool:
    mode = str(spec.get("ocr_mask_mode", spec.get("ocr_masks", ""))).strip().lower()
    return mode in {"intersecting", "overlap", "overlapping", "all_intersecting"}


def ocr_rel_masks(
    spec: dict[str, Any],
    crop_box: tuple[int, int, int, int],
    crop_size: tuple[int, int],
    ocr_records: list[dict[str, Any]],
    default_padding: int,
) -> tuple[list[tuple[int, int, int, int]], list[str], list[str]]:
    selected: list[dict[str, Any]] = []
    warnings: list[str] = []
    by_id = {str(record.get("id")): record for record in ocr_records if record.get("id")}

    for ocr_id in spec.get("ocr_mask_ids", []) or []:
        record = by_id.get(str(ocr_id))
        if record is None:
            warnings.append(f"ocr_mask_id_missing:{ocr_id}")
        else:
            selected.append(record)

    if ocr_mode_enabled(spec):
        exclude = {str(item) for item in spec.get("exclude_ocr_ids", []) or []}
        threshold = float(spec.get("ocr_overlap_threshold", 0.1))
        for record in ocr_records:
            record_id = str(record.get("id", ""))
            if record_id in exclude or record in selected:
                continue
            record_box = ocr_record_box(record)
            area = box_area(record_box)
            overlap = intersection_area(record_box, crop_box)
            if area > 0 and overlap / area >= threshold:
                selected.append(record)

    masks: list[tuple[int, int, int, int]] = []
    selected_ids: list[str] = []
    padding = int(spec.get("ocr_mask_padding", default_padding))
    for record in selected:
        record_id = str(record.get("id", ""))
        selected_ids.append(record_id)
        masks.append(
            normalize_rel_box(
                {"bbox": list(ocr_record_box(record)), "padding": padding},
                crop_box,
                crop_size,
                default_padding,
            )
        )
    return masks, selected_ids, warnings


def luminance(color: tuple[int, int, int]) -> float:
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def median_color(colors: list[tuple[int, int, int]], fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if not colors:
        return fallback
    return (
        int(median([color[0] for color in colors])),
        int(median([color[1] for color in colors])),
        int(median([color[2] for color in colors])),
    )


def sample_fill_color(
    crop: Image.Image,
    rel: tuple[int, int, int, int],
    margin: int,
    min_luminance: float | None,
    fallback: tuple[int, int, int],
) -> tuple[int, int, int]:
    rgb = crop.convert("RGB")
    x1, y1, x2, y2 = rel
    sx1 = max(0, x1 - margin)
    sy1 = max(0, y1 - margin)
    sx2 = min(rgb.width, x2 + margin)
    sy2 = min(rgb.height, y2 + margin)
    colors: list[tuple[int, int, int]] = []

    for y in range(sy1, sy2):
        for x in range(sx1, sx2):
            if x1 <= x < x2 and y1 <= y < y2:
                continue
            color = rgb.getpixel((x, y))
            if min_luminance is not None and luminance(color) < min_luminance:
                continue
            colors.append(color)
    return median_color(colors, fallback)


def apply_sample_fill(
    image: Image.Image,
    rel: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    blur: float,
    radius: int,
) -> Image.Image:
    x1, y1, x2, y2 = rel
    layer = image.copy()
    patch = Image.new("RGBA", (max(1, x2 - x1), max(1, y2 - y1)), (*fill, 255))
    layer.paste(patch, (x1, y1))

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    if radius > 0:
        draw.rounded_rectangle(rel, radius=radius, fill=255)
    else:
        draw.rectangle(rel, fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(float(blur)))
    return Image.composite(layer, image, mask)


def horizontal_inpaint_region(image: Image.Image, rel: tuple[int, int, int, int]) -> Image.Image:
    out = image.convert("RGBA").copy()
    px = out.load()
    x1, y1, x2, y2 = rel

    for y in range(y1, y2):
        left = x1 - 1
        right = x2
        while left >= 0 and px[left, y][3] == 0:
            left -= 1
        while right < out.width and px[right, y][3] == 0:
            right += 1

        if left >= 0 and right < out.width:
            left_color = px[left, y]
            right_color = px[right, y]
            span = max(right - left, 1)
            for x in range(x1, x2):
                t = (x - left) / span
                px[x, y] = tuple(
                    round(left_color[channel] * (1 - t) + right_color[channel] * t)
                    for channel in range(4)
                )
        elif left >= 0:
            for x in range(x1, x2):
                px[x, y] = px[left, y]
        elif right < out.width:
            for x in range(x1, x2):
                px[x, y] = px[right, y]
    return out


def checkerboard(size: tuple[int, int], cell: int = 10) -> Image.Image:
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(235, 235, 235))
    return image


def paste_preview(sheet: Image.Image, image: Image.Image, x: int, y: int, max_w: int, max_h: int) -> tuple[int, int]:
    rgba = image.convert("RGBA")
    scale = min(max_w / max(rgba.width, 1), max_h / max(rgba.height, 1), 1.0)
    resized = rgba.resize((max(1, round(rgba.width * scale)), max(1, round(rgba.height * scale))), Image.Resampling.LANCZOS)
    preview = checkerboard(resized.size)
    preview = Image.alpha_composite(preview.convert("RGBA"), resized).convert("RGB")
    sheet.paste(preview, (x, y))
    return resized.width, resized.height


def make_debug_sheet(records: list[dict[str, Any]], source: Image.Image, out_path: Path) -> None:
    if not records:
        return
    cell_w = 780
    cell_h = 150
    sheet = Image.new("RGB", (cell_w, cell_h * len(records)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, rec in enumerate(records):
        y = idx * cell_h
        original = source.crop(tuple(rec["source_crop_px"]))
        cleaned = Image.open(rec["output_path"]).convert("RGBA")
        paste_preview(sheet, original, 10, y + 10, 360, 94)
        paste_preview(sheet, cleaned, 400, y + 10, 360, 94)
        draw.text((10, y + 112), f"original: {rec['id']}", fill=(0, 0, 0))
        draw.text((400, y + 112), f"cleaned: {rec['strategy']} masks={rec['mask_count']}", fill=(0, 0, 0))
        draw.rectangle((0, y, cell_w - 1, y + cell_h - 1), outline=(220, 220, 220))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def make_textless(manifest_path: Path, out_dir_arg: str | None, report_arg: str | None, debug_arg: str | None) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    base = manifest_path.parent
    source_path = resolve_path(manifest["source_image"], base)
    source = Image.open(source_path).convert("RGB")
    ocr_records: list[dict[str, Any]] = []
    if manifest.get("ocr_results"):
        ocr_path = resolve_path(manifest["ocr_results"], base)
        ocr_records = load_json(ocr_path).get("records", [])
    if out_dir_arg:
        out_dir = resolve_cli_path(out_dir_arg)
    else:
        out_dir = resolve_path(manifest.get("output_dir", "textless-crops"), base)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "tool": "make_textless_crops.py",
        "manifest": str(manifest_path.resolve()),
        "source_image": str(source_path),
        "source_size_px": [source.width, source.height],
        "out_dir": str(out_dir),
        "outputs": [],
        "warnings": [],
    }

    for spec in manifest.get("crops", []):
        crop_id = str(spec["id"])
        requested_box = as_box(spec["bbox"])
        crop_box, clipped = clamp_box(requested_box, source.width, source.height)
        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            raise ValueError(f"crop {crop_id} has empty bbox after clipping: {crop_box}")

        strategy = str(spec.get("strategy", "sample-fill")).lower()
        cleaned = source.crop(crop_box).convert("RGBA")
        default_padding = int(spec.get("mask_padding", 0))
        mask_specs = spec.get("text_masks", [])
        rel_masks = [
            normalize_rel_box(mask_spec, crop_box, cleaned.size, default_padding)
            for mask_spec in mask_specs
        ]
        if (spec.get("ocr_mask_ids") or ocr_mode_enabled(spec)) and not ocr_records:
            raise ValueError(f"crop {crop_id} requested OCR masks but no ocr_results was provided")
        ocr_masks, ocr_mask_ids, ocr_warnings = ocr_rel_masks(spec, crop_box, cleaned.size, ocr_records, default_padding)
        rel_masks.extend(ocr_masks)
        for warning in ocr_warnings:
            report["warnings"].append({"id": crop_id, "warning": warning})

        for rel in rel_masks:
            if rel[2] <= rel[0] or rel[3] <= rel[1]:
                report["warnings"].append({"id": crop_id, "warning": "empty_text_mask"})
                continue
            if strategy == "horizontal-inpaint":
                cleaned = horizontal_inpaint_region(cleaned, rel)
            elif strategy == "sample-fill":
                fallback = tuple(spec.get("fallback_fill", [250, 251, 253]))
                fill = sample_fill_color(
                    cleaned,
                    rel,
                    margin=int(spec.get("sample_margin", 18)),
                    min_luminance=spec.get("min_sample_luminance"),
                    fallback=(int(fallback[0]), int(fallback[1]), int(fallback[2])),
                )
                cleaned = apply_sample_fill(
                    cleaned,
                    rel,
                    fill,
                    blur=float(spec.get("blend_blur", 2)),
                    radius=int(spec.get("blend_radius", 6)),
                )
            else:
                raise ValueError(f"unsupported textless strategy for {crop_id}: {strategy}")

        output_name = str(spec.get("output_name", f"{crop_id}.png"))
        out_path = out_dir / output_name
        cleaned.save(out_path)

        rec = {
            "id": crop_id,
            "plan_element_id": spec.get("plan_element_id"),
            "output_path": str(out_path.resolve()),
            "requested_bbox_px": list(requested_box),
            "source_crop_px": list(crop_box),
            "width": cleaned.width,
            "height": cleaned.height,
            "strategy": strategy,
            "source_kind": spec.get("source_kind", "source_textless_crop"),
            "reason": spec.get("reason"),
            "mask_count": len(rel_masks),
            "manual_mask_count": len(mask_specs),
            "ocr_mask_count": len(ocr_masks),
            "ocr_mask_ids": ocr_mask_ids,
            "relative_text_masks_px": [list(mask) for mask in rel_masks],
            "warnings": ["bbox_clipped_to_source"] if clipped else [],
        }
        report["outputs"].append(rec)
        for warning in rec["warnings"]:
            report["warnings"].append({"id": crop_id, "warning": warning})

    if debug_arg:
        debug_path = resolve_cli_path(debug_arg)
    elif manifest.get("debug_sheet"):
        debug_path = resolve_path(manifest["debug_sheet"], base)
    else:
        debug_path = out_dir / "textless_debug_sheet.png"
    make_debug_sheet(report["outputs"], source, debug_path)
    report["debug_sheet"] = str(debug_path.resolve())

    if report_arg:
        report_path = resolve_cli_path(report_arg)
    elif manifest.get("report"):
        report_path = resolve_path(manifest["report"], base)
    else:
        report_path = out_dir / "textless_report.json"
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Create textless source crops from reviewed text mask boxes.")
    parser.add_argument("manifest", help="Path to textless crop manifest JSON.")
    parser.add_argument("--out-dir", help="Output directory for textless PNG crops.")
    parser.add_argument("--report", help="Path to textless crop report JSON.")
    parser.add_argument("--debug", help="Path to side-by-side debug sheet PNG.")
    args = parser.parse_args()
    report = make_textless(Path(args.manifest).resolve(), args.out_dir, args.report, args.debug)
    print(json.dumps({"outputs": len(report["outputs"]), "warnings": len(report["warnings"]), "debug_sheet": report["debug_sheet"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
