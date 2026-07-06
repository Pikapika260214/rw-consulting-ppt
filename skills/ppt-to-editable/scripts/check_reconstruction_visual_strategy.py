#!/usr/bin/env python3
"""Check native-vs-crop decisions in a reconstruction plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from visual_strategy_rules import (  # noqa: E402
    SOURCE_CROP_STRATEGIES,
    TEXTLESS_STRATEGIES,
    full_slide_textless_background_issue,
    is_high_risk_visual_type,
    is_native_strategy,
    normalized,
)


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def slide_elements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    for slide_index, slide in enumerate(plan.get("slides", []), start=1):
        for element_index, element in enumerate(slide.get("elements", []), start=1):
            copy = dict(element)
            copy["_slide_index"] = slide_index
            copy["_element_index"] = element_index
            elements.append(copy)
    return elements


def elements_by_id(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(element.get("id")): element for element in slide_elements(plan) if element.get("id") is not None}


def strategy_regions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    review = plan.get("strategy_review")
    if isinstance(review, dict):
        for region in review.get("regions", []) or []:
            if isinstance(region, dict):
                regions.append(region)
    for slide_index, slide in enumerate(plan.get("slides", []), start=1):
        review = slide.get("strategy_review")
        if isinstance(review, dict):
            for region in review.get("regions", []) or []:
                if isinstance(region, dict):
                    copy = dict(region)
                    copy.setdefault("slide_index", slide_index)
                    regions.append(copy)
    return regions


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def is_textless_picture(element: dict[str, Any] | None) -> bool:
    if not element or element.get("type") != "picture":
        return False
    source = element.get("source") if isinstance(element.get("source"), dict) else {}
    return normalized(source.get("kind", "")) in TEXTLESS_STRATEGIES


def is_text_element(element: dict[str, Any] | None) -> bool:
    return bool(element and element.get("type") == "text")


def warning(region: dict[str, Any], warning_type: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "id": str(region.get("id", "strategy-region")),
        "warning": warning_type,
        "visual_type": region.get("visual_type"),
        "expected_strategy": region.get("expected_strategy"),
        "actual_strategy": region.get("actual_strategy"),
    }
    payload.update(extra)
    return payload


def check_region(region: dict[str, Any], element_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    region_id = str(region.get("id", "")).strip()
    visual_type = str(region.get("visual_type", "")).strip()
    expected_strategy = str(region.get("expected_strategy", "")).strip()
    actual_strategy = str(region.get("actual_strategy", "")).strip()
    evidence_ids = as_list(region.get("evidence_element_ids"))
    overlay_ids = as_list(region.get("text_overlay_element_ids"))

    if not region_id:
        warnings.append(warning(region, "strategy_region_missing_id"))
    if not visual_type:
        warnings.append(warning(region, "strategy_region_missing_visual_type"))
    if not expected_strategy:
        warnings.append(warning(region, "strategy_region_missing_expected_strategy"))
    if not actual_strategy:
        warnings.append(warning(region, "strategy_region_missing_actual_strategy"))

    expected = normalized(expected_strategy)

    for element_id in evidence_ids:
        if element_id not in element_map:
            warnings.append(warning(region, "evidence_element_missing", element_id=element_id))
    for element_id in overlay_ids:
        if element_id not in element_map:
            warnings.append(warning(region, "text_overlay_element_missing", element_id=element_id))

    high_risk = is_high_risk_visual_type(visual_type)
    if high_risk and is_native_strategy(actual_strategy):
        warnings.append(warning(region, "native_redraw_used_for_high_risk_region"))

    if expected in TEXTLESS_STRATEGIES:
        textless_evidence = [element_id for element_id in evidence_ids if is_textless_picture(element_map.get(element_id))]
        if not textless_evidence:
            warnings.append(warning(region, "expected_textless_crop_missing", evidence_element_ids=evidence_ids))

        requires_text_overlay = bool(region.get("requires_text_overlay", True))
        if requires_text_overlay:
            text_overlays = [element_id for element_id in overlay_ids if is_text_element(element_map.get(element_id))]
            if not text_overlays:
                warnings.append(warning(region, "textless_crop_text_overlay_missing", text_overlay_element_ids=overlay_ids))

    if expected in SOURCE_CROP_STRATEGIES and not evidence_ids:
        warnings.append(warning(region, "source_crop_evidence_missing"))

    return warnings


def check_plan(plan: dict[str, Any], require_strategy_review: bool = False) -> dict[str, Any]:
    regions = strategy_regions(plan)
    element_map = elements_by_id(plan)
    warnings: list[dict[str, Any]] = []

    if require_strategy_review and not regions:
        warnings.append({"id": "strategy_review", "warning": "strategy_review_missing"})

    for region in regions:
        warnings.extend(check_region(region, element_map))

    full_slide_issue = full_slide_textless_background_issue(plan)
    if full_slide_issue:
        warnings.append(
            {
                "id": "strategy_review",
                "warning": "full_slide_textless_background_disguised_as_region_crops",
                **full_slide_issue,
            }
        )

    by_type: dict[str, int] = {}
    for item in warnings:
        by_type[item["warning"]] = by_type.get(item["warning"], 0) + 1

    return {
        "tool": "check_reconstruction_visual_strategy.py",
        "status": "warnings" if warnings else "pass",
        "summary": {
            "regions": len(regions),
            "warning_count": len(warnings),
            "warnings_by_type": by_type,
        },
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check native-vs-crop visual strategy decisions.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-strategy-review", action="store_true")
    args = parser.parse_args()

    report = check_plan(load_plan(args.plan), require_strategy_review=args.require_strategy_review)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"]}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "pass" else 2)


if __name__ == "__main__":
    main()
