#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
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


def ocr_box(record: dict[str, Any]) -> tuple[float, float, float, float] | None:
    if "bbox_px" in record:
        values = record["bbox_px"]
        if len(values) != 4:
            return None
        x, y, w, h = (float(v) for v in values)
        return x, y, x + w, y + h
    if "polygon_px" in record:
        points = record["polygon_px"]
        if not points:
            return None
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return min(xs), min(ys), max(xs), max(ys)
    return None


def box_overlap_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def box_area(box: tuple[float, float, float, float]) -> float:
    return max(box[2] - box[0], 0.0) * max(box[3] - box[1], 0.0)


def load_ocr_records(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    payload = load_json(path)
    return [record for record in payload.get("records", []) if isinstance(record, dict)]


def ocr_overlap_warnings(
    crop_id: str,
    spec: dict[str, Any],
    crop_box: tuple[int, int, int, int],
    ocr_records: list[dict[str, Any]],
    default_threshold: float,
) -> list[dict[str, Any]]:
    if spec.get("allow_text_overlap"):
        return []

    allowed_ids = {str(item) for item in spec.get("allowed_ocr_ids", [])}
    threshold = float(spec.get("ocr_overlap_threshold", default_threshold))
    crop_box_float = tuple(float(value) for value in crop_box)
    warnings: list[dict[str, Any]] = []
    for record in ocr_records:
        ocr_id = str(record.get("id", ""))
        if ocr_id in allowed_ids:
            continue
        bbox = ocr_box(record)
        if not bbox:
            continue
        ocr_area = box_area(bbox)
        if ocr_area <= 0:
            continue
        overlap_ratio = box_overlap_area(crop_box_float, bbox) / ocr_area
        if overlap_ratio >= threshold:
            warnings.append(
                {
                    "id": crop_id,
                    "warning": "ocr_text_overlap",
                    "ocr_id": ocr_id,
                    "text": str(record.get("text", "")),
                    "confidence": record.get("confidence"),
                    "overlap_ratio": round(overlap_ratio, 4),
                    "ocr_bbox_px": list(bbox),
                }
            )
    return warnings


def box_from_spec(spec: dict[str, Any]) -> tuple[int, int, int, int]:
    if "bbox" in spec:
        box = as_box(spec["bbox"])
    elif "center" in spec and "size" in spec:
        cx, cy = (float(v) for v in spec["center"])
        size = spec["size"]
        if isinstance(size, list):
            if len(size) != 2:
                raise ValueError(f"size list must have two values for {spec.get('id')}")
            w, h = (float(size[0]), float(size[1]))
        else:
            w = h = float(size)
        box = (
            int(round(cx - w / 2)),
            int(round(cy - h / 2)),
            int(round(cx + w / 2)),
            int(round(cy + h / 2)),
        )
    else:
        raise ValueError(f"crop {spec.get('id', '<unknown>')} needs bbox or center+size")

    padding = int(round(float(spec.get("padding", 0))))
    if padding:
        x1, y1, x2, y2 = box
        box = (x1 - padding, y1 - padding, x2 + padding, y2 + padding)
    return box


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[tuple[int, int, int, int], bool]:
    x1, y1, x2, y2 = box
    clamped = (max(0, x1), max(0, y1), min(width, x2), min(height, y2))
    return clamped, clamped != box


def background_transparent_crop(
    source: Image.Image,
    crop_box: tuple[int, int, int, int],
    low: int = 24,
    high: int = 58,
    blur: float = 0.05,
) -> Image.Image:
    crop = source.crop(crop_box).convert("RGBA")
    px = crop.load()
    corners = [
        crop.getpixel((0, 0))[:3],
        crop.getpixel((crop.width - 1, 0))[:3],
        crop.getpixel((0, crop.height - 1))[:3],
        crop.getpixel((crop.width - 1, crop.height - 1))[:3],
    ]
    bg = tuple(sum(channel) // len(corners) for channel in zip(*corners))
    span = max(high - low, 1)

    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b, _a = px[x, y]
            dist = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if dist < low:
                alpha = 0
            elif dist < high:
                alpha = int((dist - low) / span * 255)
            else:
                alpha = 255
            px[x, y] = (r, g, b, alpha)

    if blur:
        crop = crop.filter(ImageFilter.GaussianBlur(float(blur)))
    return crop


def circular_alpha(crop: Image.Image, inset_px: float = 1.0) -> Image.Image:
    crop = crop.convert("RGBA")
    scale = 4
    big = Image.new("L", (crop.width * scale, crop.height * scale), 0)
    draw = ImageDraw.Draw(big)
    inset = float(inset_px) * scale
    draw.ellipse((inset, inset, big.width - inset, big.height - inset), fill=255)
    mask = big.resize(crop.size, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(0.15))
    crop.putalpha(mask)
    return crop


def checkerboard(size: tuple[int, int], cell: int = 10) -> Image.Image:
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(235, 235, 235))
    return image


def alpha_stats(image: Image.Image) -> dict[str, Any]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    values = alpha.tobytes()
    total = len(values)
    transparent = sum(1 for value in values if value <= 8)
    opaque = sum(1 for value in values if value >= 248)
    edge_values = []
    for x in range(rgba.width):
        edge_values.append(alpha.getpixel((x, 0)))
        edge_values.append(alpha.getpixel((x, rgba.height - 1)))
    for y in range(rgba.height):
        edge_values.append(alpha.getpixel((0, y)))
        edge_values.append(alpha.getpixel((rgba.width - 1, y)))
    edge_nontransparent = sum(1 for value in edge_values if value > 8)
    return {
        "alpha_min": min(values) if values else None,
        "alpha_max": max(values) if values else None,
        "transparent_px": transparent,
        "opaque_px": opaque,
        "nontransparent_px": total - transparent,
        "edge_nontransparent_fraction": round(edge_nontransparent / max(len(edge_values), 1), 4),
    }


def make_debug_sheet(records: list[dict[str, Any]], out_path: Path) -> None:
    if not records:
        return
    cell_w = 150
    cell_h = 132
    cols = int(records[0].get("debug_cols", 6)) if records else 6
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, rec in enumerate(records):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        crop = Image.open(rec["output_path"]).convert("RGBA")
        scale = min(92 / max(crop.width, 1), 78 / max(crop.height, 1), 2.0)
        resized = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.LANCZOS)
        preview = checkerboard(resized.size)
        preview = Image.alpha_composite(preview.convert("RGBA"), resized).convert("RGB")
        sheet.paste(preview, (x + (cell_w - resized.width) // 2, y + 8))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(220, 220, 220))
        draw.text((x + 6, y + 94), str(rec["id"])[:22], fill=(0, 0, 0))
        draw.text((x + 6, y + 112), f"{rec['width']}x{rec['height']}", fill=(90, 90, 90))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def extract(
    manifest_path: Path,
    out_dir_arg: str | None,
    report_arg: str | None,
    debug_arg: str | None,
    ocr_results_arg: str | None = None,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    base = manifest_path.parent
    source_path = resolve_path(manifest["source_image"], base)
    source = Image.open(source_path).convert("RGB")
    if ocr_results_arg:
        ocr_results_path = resolve_cli_path(ocr_results_arg)
    elif manifest.get("ocr_results"):
        ocr_results_path = resolve_path(manifest["ocr_results"], base)
    else:
        ocr_results_path = None
    ocr_records = load_ocr_records(ocr_results_path)
    default_ocr_overlap_threshold = float(manifest.get("ocr_overlap_threshold", 0.2))

    if out_dir_arg:
        out_dir = resolve_cli_path(out_dir_arg)
    else:
        out_dir = resolve_path(manifest.get("output_dir", "crops"), base)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "tool": "extract_source_crops.py",
        "manifest": str(manifest_path.resolve()),
        "source_image": str(source_path),
        "source_size_px": [source.width, source.height],
        "out_dir": str(out_dir),
        "outputs": [],
        "warnings": [],
    }

    for spec in manifest.get("crops", []):
        crop_id = str(spec["id"])
        requested_box = box_from_spec(spec)
        crop_box, clipped = clamp_box(requested_box, source.width, source.height)
        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            raise ValueError(f"crop {crop_id} has empty bbox after clipping: {crop_box}")

        alpha_mode = str(spec.get("alpha", "")).lower()
        if alpha_mode == "circle" or spec.get("circular"):
            alpha_inset_px = float(spec.get("alpha_inset_px", spec.get("circle_inset_px", 1.0)))
            crop = circular_alpha(source.crop(crop_box), alpha_inset_px)
        elif spec.get("transparent") or alpha_mode == "background":
            alpha_inset_px = None
            thresholds = spec.get("transparent_thresholds", {})
            crop = background_transparent_crop(
                source,
                crop_box,
                low=int(thresholds.get("low", spec.get("transparent_low", 24))),
                high=int(thresholds.get("high", spec.get("transparent_high", 58))),
                blur=float(thresholds.get("blur", spec.get("transparent_blur", 0.05))),
            )
        else:
            alpha_inset_px = None
            crop = source.crop(crop_box).convert("RGBA")

        output_name = str(spec.get("output_name", f"{crop_id}.png"))
        out_path = out_dir / output_name
        crop.save(out_path)

        warnings: list[str] = []
        if clipped:
            warnings.append("bbox_clipped_to_source")
        if spec.get("expect_square") and crop.width != crop.height:
            warnings.append("not_square")
        stats = alpha_stats(crop)
        if (spec.get("transparent") or alpha_mode in {"background", "circle"}) and stats["edge_nontransparent_fraction"] > 0.15:
            warnings.append("nontransparent_pixels_touch_crop_edge")
        ocr_warnings = ocr_overlap_warnings(
            crop_id,
            spec,
            crop_box,
            ocr_records,
            default_ocr_overlap_threshold,
        )
        if ocr_warnings:
            warnings.append("ocr_text_overlap")

        rec = {
            "id": crop_id,
            "plan_element_id": spec.get("plan_element_id"),
            "output_path": str(out_path.resolve()),
            "requested_bbox_px": list(requested_box),
            "source_crop_px": list(crop_box),
            "width": crop.width,
            "height": crop.height,
            "alpha_mode": alpha_mode or ("background" if spec.get("transparent") else "plain"),
            "alpha_inset_px": alpha_inset_px,
            "source_kind": spec.get("source_kind"),
            "reason": spec.get("reason"),
            "warnings": warnings,
            **stats,
        }
        report["outputs"].append(rec)
        for warning in warnings:
            if warning != "ocr_text_overlap":
                report["warnings"].append({"id": crop_id, "warning": warning})
        report["warnings"].extend(ocr_warnings)

    if debug_arg:
        debug_path = resolve_cli_path(debug_arg)
    elif manifest.get("debug_sheet"):
        debug_path = resolve_path(manifest["debug_sheet"], base)
    else:
        debug_path = out_dir / "crop_debug_sheet.png"
    make_debug_sheet(report["outputs"], debug_path)
    report["debug_sheet"] = str(debug_path.resolve())

    if report_arg:
        report_path = resolve_cli_path(report_arg)
    elif manifest.get("report"):
        report_path = resolve_path(manifest["report"], base)
    else:
        report_path = out_dir / "crop_report.json"
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract source-derived crops from a reviewed crop manifest.")
    parser.add_argument("manifest", help="Path to crop manifest JSON.")
    parser.add_argument("--out-dir", help="Output directory for PNG crops.")
    parser.add_argument("--report", help="Path to crop report JSON.")
    parser.add_argument("--debug", help="Path to debug sheet PNG.")
    parser.add_argument("--ocr-results", help="Optional OCR results JSON for crop/text overlap warnings.")
    args = parser.parse_args()
    report = extract(Path(args.manifest).resolve(), args.out_dir, args.report, args.debug, args.ocr_results)
    print(json.dumps({"outputs": len(report["outputs"]), "warnings": len(report["warnings"]), "debug_sheet": report["debug_sheet"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
