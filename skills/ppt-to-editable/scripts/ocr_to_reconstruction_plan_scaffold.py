#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def font_size_from_bbox(height_px: float, image_height_px: float, slide_height_in: float) -> float:
    height_in = max(0.05, height_px / image_height_px * slide_height_in)
    return max(6.0, min(34.0, round(height_in * 72.0 * 0.72, 1)))


def normalize_bbox(record: dict[str, Any]) -> tuple[float, float, float, float]:
    if "bbox_px" in record:
        x, y, w, h = [float(value) for value in record["bbox_px"]]
        return x, y, w, h
    if "source_bbox_px" in record:
        x1, y1, x2, y2 = [float(value) for value in record["source_bbox_px"]]
        return x1, y1, max(1.0, x2 - x1), max(1.0, y2 - y1)
    raise ValueError(f"OCR record lacks bbox_px/source_bbox_px: {record.get('id')}")


def record_id(record: dict[str, Any], idx: int) -> str:
    return str(record.get("id") or f"ocr_{idx:04d}")


def build_scaffold(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    ocr = load_json(args.ocr_results)
    image_width_px, image_height_px = [float(value) for value in ocr["image_size_px"]]
    elements: list[dict[str, Any]] = []
    review_records: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []

    for idx, record in enumerate(ocr.get("records", []), start=1):
        rid = record_id(record, idx)
        confidence = float(record.get("confidence", 0))
        text = str(record.get("text", "")).strip()
        x_px, y_px, w_px, h_px = normalize_bbox(record)
        bbox_px = [round(x_px), round(y_px), round(w_px), round(h_px)]

        if not text or confidence < args.min_confidence:
            omitted.append(
                {
                    "ocr_id": rid,
                    "reason": "low_confidence_or_empty",
                    "confidence": confidence,
                    "text": text,
                    "bbox_px": bbox_px,
                }
            )
            continue

        x = round(x_px / image_width_px * args.slide_width_in, 4)
        y = round(y_px / image_height_px * args.slide_height_in, 4)
        w = round(w_px / image_width_px * args.slide_width_in, 4)
        h = round(max(h_px / image_height_px * args.slide_height_in, 0.12), 4)
        element_id = f"{rid}_text"
        element = {
            "id": element_id,
            "type": "text",
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "text": text,
            "font_size": font_size_from_bbox(h_px, image_height_px, args.slide_height_in),
            "font_face": args.font_face,
            "color": "#111111",
            "bold": False,
            "align": "left",
            "valign": "top",
            "margin": 0.01,
            "word_wrap": False,
            "semantic_block": False,
            "trace_level": "line",
            "source": {
                "kind": "ocr_scaffold",
                "ocr_id": rid,
                "confidence": confidence,
                "bbox_px": bbox_px,
                "polygon_px": record.get("polygon_px"),
                "review_status": "needs_review",
            },
        }
        elements.append(element)
        review_records.append(
            {
                "ocr_id": rid,
                "proposed_element_id": element_id,
                "text": text,
                "confidence": confidence,
                "bbox_px": bbox_px,
                "review_status": "needs_review",
                "allowed_actions": ["accept", "correct", "omit", "merge_into_semantic_block", "keep_in_background"],
            }
        )

    plan = {
        "title": args.title,
        "mode": "mixed_reconstruction",
        "slide_width_in": args.slide_width_in,
        "slide_height_in": args.slide_height_in,
        "source_image": str(args.source_image),
        "source_ocr": str(args.ocr_results),
        "status": "draft_needs_review",
        "notes": [
            "This is an OCR-derived text scaffold, not a final reconstruction plan.",
            "Do not package this scaffold as final until every OCR text element is reviewed.",
            "Geometry is OCR-derived in pixels and mapped mechanically to slide inches.",
            "Native shapes and tight source crops are not generated in this scaffold.",
        ],
        "summary": {
            "ocr_records": len(ocr.get("records", [])),
            "text_elements": len(elements),
            "omitted": len(omitted),
            "min_confidence": args.min_confidence,
        },
        "slides": [
            {
                "id": args.slide_id,
                "elements": elements,
            }
        ],
        "omitted_records": omitted,
    }
    review_manifest = {
        "title": f"{args.title} review manifest",
        "source_image": str(args.source_image),
        "source_ocr": str(args.ocr_results),
        "status": "needs_human_or_agent_review",
        "summary": plan["summary"],
        "records": review_records,
        "omitted_records": omitted,
    }
    return plan, review_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a reviewed-required reconstruction text scaffold from OCR geometry.")
    parser.add_argument("ocr_results", type=Path, help="OCR results JSON with image_size_px and records.")
    parser.add_argument("--out", type=Path, required=True, help="Output source_reconstruction_plan scaffold JSON.")
    parser.add_argument("--review-manifest", type=Path, help="Output OCR review manifest JSON.")
    parser.add_argument("--source-image", type=Path, required=True, help="Source image path to store in the scaffold.")
    parser.add_argument("--slide-id", default="ocr-scaffold", help="Slide id to use in the scaffold.")
    parser.add_argument("--title", default="OCR-derived reconstruction plan scaffold", help="Plan title.")
    parser.add_argument("--slide-width-in", type=float, default=13.333333)
    parser.add_argument("--slide-height-in", type=float, default=7.5)
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--font-face", default="Microsoft YaHei")
    args = parser.parse_args()

    args.ocr_results = args.ocr_results.resolve()
    plan, review_manifest = build_scaffold(args)
    write_json(args.out.resolve(), plan)
    if args.review_manifest:
        write_json(args.review_manifest.resolve(), review_manifest)
    print(json.dumps(plan["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
