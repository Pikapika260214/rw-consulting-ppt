#!/usr/bin/env python3
"""Inspect a PPTX for editable text, picture, no-wrap, and native-line counts."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


FULL_W = "12192000"
FULL_H = "6858000"


def slide_sort_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def inspect_pptx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as z:
        slide_names = sorted(
            [
                name
                for name in z.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ],
            key=slide_sort_key,
        )
        slides: list[dict[str, Any]] = []
        totals = {
            "slides": len(slide_names),
            "pictures": 0,
            "fullSlidePictures": 0,
            "editableTextBodies": 0,
            "textShapes": 0,
            "nativeShapes": 0,
            "nativeTables": 0,
            "nativeTableCells": 0,
            "nativeTableTextCells": 0,
            "noWrapTextBodies": 0,
            "autoWrapTextBodies": 0,
            "noAutofitTextBodies": 0,
            "autofitTextBodies": 0,
            "nativeDashedLines": 0,
        }
        for idx, name in enumerate(slide_names, start=1):
            xml = z.read(name).decode("utf-8", errors="ignore")
            pictures = xml.count("<p:pic>")
            sp_blocks = re.findall(r"<p:sp>.*?</p:sp>", xml, flags=re.DOTALL)
            table_blocks = re.findall(r"<a:tbl>.*?</a:tbl>", xml, flags=re.DOTALL)
            table_cell_blocks = re.findall(r"<a:tc>.*?</a:tc>", xml, flags=re.DOTALL)
            text_body_blocks = re.findall(r"<p:txBody>.*?</p:txBody>", xml, flags=re.DOTALL)
            text_bodies = sum(1 for block in text_body_blocks if re.search(r"<a:t>.+?</a:t>", block, flags=re.DOTALL))
            text_shapes = len(sp_blocks)
            native_tables = len(table_blocks)
            table_text_cells = sum(1 for block in table_cell_blocks if re.search(r"<a:t>.+?</a:t>", block, flags=re.DOTALL))
            no_wrap = xml.count('wrap="none"')
            auto_wrap = xml.count('wrap="square"') + xml.count('wrap="1"')
            no_autofit = xml.count("<a:noAutofit")
            autofit = xml.count("<a:spAutoFit") + xml.count("<a:normAutofit")
            dashed = len(re.findall(r"<a:prstDash\b(?![^>]*val=\"solid\")", xml))
            pic_blocks = re.findall(r"<p:pic>.*?</p:pic>", xml, flags=re.DOTALL)
            full_slide_pictures = sum(
                1 for block in pic_blocks if f'<a:ext cx="{FULL_W}" cy="{FULL_H}"/>' in block
            )
            native_shapes = max(0, text_shapes - text_bodies)
            slide_report = {
                "slide": idx,
                "pictures": pictures,
                "fullSlidePictures": full_slide_pictures,
                "editableTextBodies": text_bodies,
                "textShapes": text_shapes,
                "nativeShapes": native_shapes,
                "nativeTables": native_tables,
                "nativeTableCells": len(table_cell_blocks),
                "nativeTableTextCells": table_text_cells,
                "noWrapTextBodies": no_wrap,
                "autoWrapTextBodies": auto_wrap,
                "noAutofitTextBodies": no_autofit,
                "autofitTextBodies": autofit,
                "nativeDashedLines": dashed,
            }
            slides.append(slide_report)
            for key in totals:
                if key != "slides":
                    totals[key] += int(slide_report[key])
    return {"pptx": str(path), "summary": totals, "slides": slides}


def load_manifest(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def manifest_stats(manifest: dict[str, Any] | None) -> dict[str, int]:
    if not manifest:
        return {}
    stats = {
        "manifestSlides": 0,
        "manifestTextBoxes": 0,
        "manifestLineTraceBoxes": 0,
        "manifestAcceptedLineTraceBoxes": 0,
        "manifestOmittedBoxes": 0,
    }
    slides = manifest.get("slides") or []
    stats["manifestSlides"] = len(slides)
    for slide in slides:
        for box in slide.get("text_boxes") or []:
            stats["manifestTextBoxes"] += 1
            if box.get("trace_level") == "line":
                stats["manifestLineTraceBoxes"] += 1
                if box.get("review_status", "accepted") == "accepted":
                    stats["manifestAcceptedLineTraceBoxes"] += 1
            if box.get("review_status") == "omit" or box.get("omit_reason"):
                stats["manifestOmittedBoxes"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect PPTX editability structure.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--manifest", type=Path, help="Optional text_layout_manifest.json")
    parser.add_argument("--out", type=Path, help="Write JSON report")
    args = parser.parse_args()

    report = inspect_pptx(args.pptx)
    stats = manifest_stats(load_manifest(args.manifest))
    if stats:
        report["manifest"] = stats
        report["checks"] = {
            "slide_count_matches_manifest": report["summary"]["slides"] == stats["manifestSlides"],
            "text_body_count_matches_manifest": report["summary"]["editableTextBodies"] == stats["manifestTextBoxes"],
            "line_trace_no_wrap_complete": report["summary"]["noWrapTextBodies"] >= stats["manifestLineTraceBoxes"],
            "line_trace_no_autofit_complete": report["summary"]["noAutofitTextBodies"] >= stats["manifestLineTraceBoxes"],
        }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for key, value in report["summary"].items():
        print(f"{key}={value}")
    if stats:
        for key, value in stats.items():
            print(f"{key}={value}")
        for key, value in report["checks"].items():
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
