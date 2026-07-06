#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rel_path(path: Path, base: Path) -> str:
    return os.path.relpath(path.resolve(), base.resolve()).replace(os.sep, "/")


def iter_elements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    for slide in plan.get("slides", []):
        for element in slide.get("elements", []):
            elements.append(element)
    return elements


def candidate_ids(crop: dict[str, Any]) -> list[str]:
    crop_id = str(crop.get("id", ""))
    explicit = crop.get("plan_element_id")
    candidates = []
    if explicit:
        candidates.append(str(explicit))
    candidates.extend(
        [
            crop_id,
            f"{crop_id}-icon",
            f"{crop_id}-background",
            f"{crop_id}-bg",
            f"{crop_id}-flow-bg",
            f"{crop_id}-card-bg",
        ]
    )
    seen: set[str] = set()
    return [item for item in candidates if item and not (item in seen or seen.add(item))]


def find_picture_element(elements_by_id: dict[str, dict[str, Any]], crop: dict[str, Any]) -> dict[str, Any] | None:
    for candidate in candidate_ids(crop):
        element = elements_by_id.get(candidate)
        if element and element.get("type") == "picture":
            return element
    return None


def apply_crop_report(plan_path: Path, crop_report_paths: list[Path], out_path: Path, report_path: Path, strict: bool) -> dict[str, Any]:
    plan = load_json(plan_path)
    plan_base = out_path.parent
    elements = iter_elements(plan)
    elements_by_id = {str(element.get("id")): element for element in elements if element.get("id")}

    sync_report: dict[str, Any] = {
        "tool": "apply_crop_report_to_plan.py",
        "plan": str(plan_path.resolve()),
        "out": str(out_path.resolve()),
        "crop_reports": [str(path.resolve()) for path in crop_report_paths],
        "updated": [],
        "warnings": [],
    }

    for crop_report_path in crop_report_paths:
        crop_report = load_json(crop_report_path)
        for crop in crop_report.get("outputs", []):
            element = find_picture_element(elements_by_id, crop)
            if element is None:
                warning = {
                    "crop_id": crop.get("id"),
                    "warning": "no_matching_picture_element",
                    "candidate_ids": candidate_ids(crop),
                }
                sync_report["warnings"].append(warning)
                if strict:
                    raise ValueError(f"no matching picture element for crop {crop.get('id')}")
                continue

            output_path = Path(crop["output_path"])
            old_path = element.get("path")
            element["path"] = rel_path(output_path, plan_base)
            source = element.setdefault("source", {})
            source.setdefault("kind", crop.get("source_kind") or ("source_textless_crop" if "textless" in crop_report.get("tool", "") else "source_crop"))
            if crop.get("source_crop_px"):
                source["source_crop_px"] = crop["source_crop_px"]
            if crop.get("reason"):
                source["reason"] = crop["reason"]
            source["crop_report"] = rel_path(crop_report_path, plan_base)

            sync_report["updated"].append(
                {
                    "crop_id": crop.get("id"),
                    "element_id": element.get("id"),
                    "old_path": old_path,
                    "new_path": element["path"],
                    "source_crop_px": crop.get("source_crop_px"),
                }
            )

    write_json(out_path, plan)
    write_json(report_path, sync_report)
    return sync_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply crop report outputs to matching picture elements in a reconstruction plan.")
    parser.add_argument("plan", help="Input source_reconstruction_plan.json.")
    parser.add_argument("--crop-report", action="append", required=True, help="Crop or textless report JSON. May be repeated.")
    parser.add_argument("--out", required=True, help="Output patched reconstruction plan JSON.")
    parser.add_argument("--report", required=True, help="Output sync report JSON.")
    parser.add_argument("--strict", action="store_true", help="Fail if any crop output cannot be matched to a picture element.")
    args = parser.parse_args()
    result = apply_crop_report(
        Path(args.plan).resolve(),
        [Path(path).resolve() for path in args.crop_report],
        Path(args.out).resolve(),
        Path(args.report).resolve(),
        strict=args.strict,
    )
    print(json.dumps({"updated": len(result["updated"]), "warnings": len(result["warnings"]), "out": str(Path(args.out).resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
