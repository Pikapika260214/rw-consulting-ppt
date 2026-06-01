#!/usr/bin/env python3
"""Run RapidOCR on slide images and save normalized OCR geometry."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def add_local_deps(deps: Path | None) -> None:
    if not deps:
        return
    deps = deps.resolve()
    if not deps.exists():
        return
    for subdir in ("shapely.libs", "numpy.libs", os.path.join("onnxruntime", "capi")):
        dll_dir = deps / subdir
        if dll_dir.exists() and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(dll_dir))
    sys.path.insert(0, str(deps))


def normalize_result(raw_result: list[Any] | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_result or [], start=1):
        polygon = [[float(x), float(y)] for x, y in item[0]]
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        x1, y1 = min(xs), min(ys)
        x2, y2 = max(xs), max(ys)
        records.append(
            {
                "id": f"ocr_{idx:03d}",
                "text": str(item[1]),
                "confidence": float(item[2]),
                "polygon_px": polygon,
                "bbox_px": [round(x1, 2), round(y1, 2), round(x2 - x1, 2), round(y2 - y1, 2)],
            }
        )
    return records


def draw_overlay(source: Path, records: list[dict[str, Any]], out: Path) -> None:
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    for record in records:
        polygon = [tuple(point) for point in record["polygon_px"]]
        draw.line(polygon + [polygon[0]], fill=(220, 38, 38), width=2)
        x, y, _, _ = record["bbox_px"]
        draw.rectangle((x, max(0, y - 14), x + 52, y), fill=(220, 38, 38))
        draw.text((x + 3, max(0, y - 13)), record["id"].replace("ocr_", ""), fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RapidOCR and export slide text geometry.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--deps", type=Path, default=Path(".deps/ppt-to-editable-ocr"))
    args = parser.parse_args()

    add_local_deps(args.deps)
    from rapidocr_onnxruntime import RapidOCR

    ocr = RapidOCR()
    raw_result, elapsed = ocr(str(args.source))
    records = normalize_result(raw_result)

    payload = {
        "source": str(args.source.resolve()),
        "image_size_px": list(Image.open(args.source).size),
        "engine": "rapidocr_onnxruntime",
        "elapsed": elapsed,
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.overlay:
        draw_overlay(args.source, records, args.overlay)

    print(json.dumps({"records": len(records), "out": str(args.out), "overlay": str(args.overlay) if args.overlay else None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
