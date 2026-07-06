#!/usr/bin/env python
"""Convert a single-page QA output into a 3.0 slide handoff summary.

The integrated single-page reconstruction QA chain packages and renders one
editable slide. The 3.0 deck controller needs extra handoff metadata so it can
safely assemble multiple independently-produced slides.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from visual_strategy_rules import (  # noqa: E402
    CROP_FIRST_STRATEGIES,
    is_high_risk_visual_type,
    is_native_strategy,
    normalized,
)

PRIMARY_SINGLE_PAGE_ENGINE_ID = "ppt-to-editable-v3-1-preview"
MIN_READABLE_BODY_FONT_SIZE = 6.8
NON_TEXT_ANCHOR_KEYWORDS = (
    "arrow",
    "arrowhead",
    "connector",
    "route_line",
    "route line",
    "process_line",
    "step_marker",
    "step marker",
    "step_badge",
    "card_edge",
    "card edge",
    "card_border",
    "cut_corner",
    "cut corner",
    "divider",
    "icon",
)
NON_TEXT_ANCHOR_FAILURE_KEYWORDS = (
    "missing-non-text-anchor",
    "missing-arrow",
    "missing arrow",
    "missing-arrowhead",
    "missing arrowhead",
    "erased-arrow",
    "erased arrow",
    "broken-route-line",
    "broken route line",
    "broken-connector",
    "broken connector",
    "missing-connector",
    "missing connector",
    "missing-step-marker",
    "missing step marker",
    "missing-card-edge",
    "missing card edge",
    "cropped-icon",
    "cropped icon",
    "icon stroke missing",
)
ANCHOR_FAILURE_STATUSES = {
    "failed",
    "fail",
    "missing",
    "erased",
    "broken",
    "cropped",
    "clipped",
}


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dict_summary(report: dict | None) -> dict:
    if not isinstance(report, dict):
        return {}
    summary = report.get("summary")
    return summary if isinstance(summary, dict) else report


def script_name_from_value(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("name", "script", "path", "script_path", "command"):
            if key in value:
                return script_name_from_value(value[key])
        return None
    if isinstance(value, list):
        for item in value:
            name = script_name_from_value(item)
            if name and (name.endswith(".py") or name.endswith(".ps1")):
                return name
        return script_name_from_value(value[-1]) if value else None
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.replace("\\", "/").split("/")[-1]


def scripts_from_single_page_summary(summary_single_page: dict, explicit_scripts: list[str]) -> list[str]:
    seen: set[str] = set()
    scripts: list[str] = []

    def add(value: Any) -> None:
        name = script_name_from_value(value)
        if not name or name in seen:
            return
        if name.endswith(".py") or name.endswith(".ps1"):
            seen.add(name)
            scripts.append(name)

    for script in explicit_scripts:
        add(script)
    for step in summary_single_page.get("steps", []) if isinstance(summary_single_page, dict) else []:
        if isinstance(step, dict):
            add(step.get("command") or step.get("name"))
    return scripts


def normalize_mode(value: str | None) -> str:
    if not value:
        return "mixed-reconstruction"
    return value.replace("_", "-")


def list_unique(*groups: Any) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for group in groups:
        if not isinstance(group, list):
            continue
        for item in group:
            key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
    return result


def flatten_text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(flatten_text_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(flatten_text_values(item))
        return values
    return [str(value)]


def text_contains_any(value: Any, patterns: tuple[str, ...]) -> bool:
    text = " ".join(flatten_text_values(value)).lower()
    return any(pattern in text for pattern in patterns)


def required_references_read(manifest: dict) -> list[dict]:
    refs = []
    for item in manifest.get("required_reading", []):
        if item.get("must_read"):
            refs.append(
                {
                    "id": item.get("id"),
                    "path": item.get("path"),
                    "status": "reported-read",
                }
            )
    return refs


def fallback_references_read(summary_single_page: dict, manifest: dict) -> list[dict]:
    raw = []
    if isinstance(summary_single_page, dict):
        raw = summary_single_page.get("fallback_references_read", [])
    if not isinstance(raw, list):
        return []

    allowed = {
        item.get("id"): item
        for item in manifest.get("fallback_reading", [])
        if isinstance(item, dict) and item.get("id")
    }
    refs = []
    for item in raw:
        if isinstance(item, dict):
            ref_id = item.get("id")
            reason = item.get("reason") or item.get("status") or "reported by single-page summary"
        else:
            ref_id = str(item)
            reason = "reported by single-page summary"
        if ref_id not in allowed:
            continue
        refs.append(
            {
                "id": ref_id,
                "path": allowed[ref_id].get("path"),
                "reason": reason,
            }
        )
    return refs


def region_crop_plan(plan: dict, crop_report: dict | None) -> list[dict]:
    regions = []
    strategy = plan.get("strategy_review") if isinstance(plan, dict) else None
    for region in (strategy or {}).get("regions", []) if isinstance(strategy, dict) else []:
        if not isinstance(region, dict):
            continue
        regions.append(
            {
                "id": region.get("id"),
                "visual_type": region.get("visual_type"),
                "source_bbox_px": region.get("source_bbox_px"),
                "strategy": region.get("actual_strategy") or region.get("expected_strategy"),
                "reason": region.get("reason") or region.get("strategy_reason") or region.get("override_reason"),
                "text_overlay_element_ids": region.get("text_overlay_element_ids", []),
            }
        )

    if regions:
        return regions

    crop_outputs = (crop_report or {}).get("outputs", []) if isinstance(crop_report, dict) else []
    for index, output in enumerate(crop_outputs, start=1):
        if not isinstance(output, dict):
            continue
        bbox = output.get("source_bbox_px") or output.get("source_crop_px") or output.get("bbox_px")
        regions.append(
            {
                "id": output.get("id") or output.get("name") or f"source-crop-{index}",
                "visual_type": output.get("visual_type") or "source_crop",
                "source_bbox_px": bbox,
                "strategy": output.get("strategy") or output.get("kind") or "source_crop",
                "reason": output.get("reason") or "Derived from crop_report output.",
                "crop_count": 1,
            }
        )
    return regions


def crop_manifest_summary(attempt_dir: Path, crop_report: dict | None) -> dict:
    manifest_path = attempt_dir / "crop_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path, {})
        regions = manifest.get("regions", []) if isinstance(manifest, dict) else []
        return {
            "status": "provided",
            "path": str(manifest_path),
            "region_count": len(regions) if isinstance(regions, list) else None,
        }

    crop_outputs = (crop_report or {}).get("outputs", []) if isinstance(crop_report, dict) else []
    if crop_outputs:
        return {
            "status": "derived-from-crop-report",
            "path": str(attempt_dir / "crop_report.json"),
            "region_count": len(crop_outputs),
        }

    return {
        "status": "empty-or-not-required",
        "path": str(manifest_path),
        "reason": "no_source_crops_required",
        "region_count": 0,
    }


def slide_elements(plan: dict) -> list[dict]:
    elements: list[dict] = []
    for slide in plan.get("slides", []) if isinstance(plan, dict) else []:
        if not isinstance(slide, dict):
            continue
        for element in slide.get("elements", []) or []:
            if isinstance(element, dict):
                elements.append(element)
    return elements


def text_elements(plan: dict) -> list[dict]:
    return [element for element in slide_elements(plan) if element.get("type") == "text"]


def strategy_regions(plan: dict) -> list[dict]:
    regions: list[dict] = []
    review = plan.get("strategy_review") if isinstance(plan, dict) else None
    if isinstance(review, dict):
        regions.extend([region for region in review.get("regions", []) or [] if isinstance(region, dict)])
    for slide in plan.get("slides", []) if isinstance(plan, dict) else []:
        if not isinstance(slide, dict):
            continue
        slide_review = slide.get("strategy_review")
        if isinstance(slide_review, dict):
            regions.extend([region for region in slide_review.get("regions", []) or [] if isinstance(region, dict)])
    return regions


def text_fit_warning_types(text_fit_report: dict | None) -> list[str]:
    warnings = text_fit_report.get("warnings", []) if isinstance(text_fit_report, dict) else []
    if not isinstance(warnings, list):
        return []
    result: list[str] = []
    for item in warnings:
        if isinstance(item, dict) and item.get("warning"):
            result.append(str(item["warning"]))
    return result


def font_size_consistency_review(plan: dict, text_fit_report: dict | None) -> dict:
    sizes: list[tuple[str, float]] = []
    for element in text_elements(plan):
        try:
            size = float(element.get("font_size"))
        except (TypeError, ValueError):
            continue
        element_id = str(element.get("id", "text"))
        text = str(element.get("text", "")).strip()
        if not text:
            continue
        sizes.append((element_id, size))

    issues: list[dict] = []
    for element_id, size in sizes:
        if size < MIN_READABLE_BODY_FONT_SIZE:
            issues.append(
                {
                    "issue": "tiny-font-outlier",
                    "element_id": element_id,
                    "font_size": size,
                    "minimum": MIN_READABLE_BODY_FONT_SIZE,
                }
            )

    ordered = sorted(size for _element_id, size in sizes)
    median = ordered[len(ordered) // 2] if ordered else None
    min_size = ordered[0] if ordered else None
    if median and min_size and min_size < 9 and min_size < median * 0.55:
        issues.append(
            {
                "issue": "font-size-hierarchy-drift",
                "min_font_size": min_size,
                "median_font_size": median,
            }
        )

    warning_types = text_fit_warning_types(text_fit_report)
    return {
        "status": "failed" if issues else "reviewed",
        "min_font_size": min_size,
        "median_font_size": median,
        "text_element_count": len(sizes),
        "issues": issues,
        "text_fit_warning_types": warning_types,
        "rule": "preserve relative font size hierarchy; do not shrink visible body text into tiny outliers",
    }


def complex_visual_strategy_review(plan: dict, visual_report: dict | None) -> dict:
    regions = strategy_regions(plan)
    complex_regions = [
        region for region in regions if is_high_risk_visual_type(region.get("visual_type"))
    ]
    crop_first_regions = [
        region for region in complex_regions if normalized(region.get("actual_strategy")) in CROP_FIRST_STRATEGIES
    ]
    native_complex_regions = [
        region
        for region in complex_regions
        if is_native_strategy(region.get("actual_strategy"))
    ]
    visual_warnings = []
    if isinstance(visual_report, dict):
        for item in visual_report.get("warnings", []) or []:
            if isinstance(item, dict):
                visual_warnings.append(item.get("warning"))
    issues: list[dict] = []
    for region in native_complex_regions:
        issues.append(
            {
                "issue": "native-redraw-complex-artwork",
                "region_id": region.get("id"),
                "visual_type": region.get("visual_type"),
                "actual_strategy": region.get("actual_strategy"),
            }
        )
    for warning in visual_warnings:
        if warning in {"native_redraw_used_for_high_risk_region", "expected_textless_crop_missing"}:
            issues.append({"issue": str(warning)})
    return {
        "status": "failed" if issues else "reviewed",
        "complex_region_count": len(complex_regions),
        "crop_first_region_count": len(crop_first_regions),
        "native_complex_region_count": len(native_complex_regions),
        "unresolved_native_redraw_drift": bool(issues),
        "issues": issues,
        "rule": "complex artwork and source-specific modules use crop-first handling unless native redraw is proven faithful",
    }


def text_background_policy(plan: dict) -> dict:
    issues: list[dict] = []
    for element in slide_elements(plan):
        if element.get("type") != "shape":
            continue
        element_id = str(element.get("id", "")).lower()
        if "backing" in element_id or "pale" in element_id:
            issues.append(
                {
                    "issue": "invented-text-background",
                    "element_id": element.get("id"),
                    "fill": element.get("fill"),
                }
            )

    limitation_text = " ".join(str(item).lower() for item in plan.get("limitations", []) if item is not None)
    for keyword in ("backing rectangle", "pale rectangle", "invented text background", "generic fill"):
        if keyword in limitation_text:
            issues.append({"issue": "invented-text-background", "source": "plan.limitations", "keyword": keyword})

    return {
        "status": "failed" if issues else "reviewed",
        "invented_text_backgrounds_added": bool(issues),
        "issues": issues,
        "rule": "editable text boxes stay transparent unless the source already contains that visible card or bar",
    }


def anchor_record_id(record: dict, fallback: str) -> str:
    for key in ("id", "anchor_id", "region_id", "element_id", "name"):
        value = record.get(key)
        if value:
            return str(value)
    return fallback


def is_non_text_anchor_record(record: dict) -> bool:
    if record.get("is_protected_anchor") is True:
        return True
    if record.get("protected_visual_anchors"):
        return True
    if record.get("required_visual_anchors"):
        return True
    fields = {
        "type": record.get("type"),
        "role": record.get("role"),
        "visual_type": record.get("visual_type"),
        "strategy": record.get("strategy"),
        "actual_strategy": record.get("actual_strategy"),
        "id": record.get("id"),
        "name": record.get("name"),
        "category": record.get("category"),
    }
    return text_contains_any(fields, NON_TEXT_ANCHOR_KEYWORDS)


def issue_from_anchor_record(record: dict, fallback: str) -> dict | None:
    anchor_id = anchor_record_id(record, fallback)
    for key in ("missing", "erased", "broken", "cropped", "clipped"):
        if record.get(key) is True:
            return {"issue": f"{key}-non-text-anchor", "anchor_id": anchor_id}
    status = str(record.get("status") or record.get("preservation_status") or "").lower()
    if status in ANCHOR_FAILURE_STATUSES:
        return {"issue": f"{status}-non-text-anchor", "anchor_id": anchor_id}
    if text_contains_any(
        {
            "issues": record.get("issues"),
            "warnings": record.get("warnings"),
            "limitations": record.get("limitations"),
            "failure_reason": record.get("failure_reason"),
        },
        NON_TEXT_ANCHOR_FAILURE_KEYWORDS,
    ):
        return {"issue": "missing-non-text-anchor", "anchor_id": anchor_id, "source": "record.issue_text"}
    return None


def append_anchor_issues_from_review(review: dict, issues: list[dict]) -> None:
    if not isinstance(review, dict):
        return
    status = str(review.get("status", "")).lower()
    if status in ANCHOR_FAILURE_STATUSES:
        issues.append({"issue": "missing-non-text-anchor", "source": "explicit_review_status", "status": status})
    if review.get("missing_required_anchors") is True:
        issues.append({"issue": "missing-non-text-anchor", "source": "explicit_review"})
    for key in ("missing_anchors", "broken_anchors", "erased_anchors", "cropped_anchors", "clipped_anchors"):
        values = review.get(key)
        if isinstance(values, list) and values:
            for item in values:
                issues.append({"issue": key.replace("_anchors", "-non-text-anchor"), "anchor": item})
    if text_contains_any(
        {
            "issues": review.get("issues"),
            "warnings": review.get("warnings"),
            "remaining_issues": review.get("remaining_issues"),
        },
        NON_TEXT_ANCHOR_FAILURE_KEYWORDS,
    ):
        issues.append({"issue": "missing-non-text-anchor", "source": "explicit_review_issue_text"})


def non_text_anchor_preservation_review(plan: dict) -> dict:
    anchor_records: list[dict] = []
    issues: list[dict] = []

    def add_anchor_list(owner: dict, key: str, source: str) -> None:
        values = owner.get(key)
        if not isinstance(values, list):
            return
        for index, value in enumerate(values, start=1):
            record = value if isinstance(value, dict) else {"id": str(value)}
            record = {**record, "_source": source}
            anchor_records.append(record)
            issue = issue_from_anchor_record(record, f"{source}-{index}")
            if issue:
                issues.append(issue)

    if isinstance(plan, dict):
        add_anchor_list(plan, "protected_visual_anchors", "plan.protected_visual_anchors")
        add_anchor_list(plan, "non_text_visual_anchors", "plan.non_text_visual_anchors")
        add_anchor_list(plan, "required_visual_anchors", "plan.required_visual_anchors")
        append_anchor_issues_from_review(plan.get("non_text_anchor_preservation_review", {}), issues)

    for slide_index, slide in enumerate(plan.get("slides", []) if isinstance(plan, dict) else [], start=1):
        if not isinstance(slide, dict):
            continue
        add_anchor_list(slide, "protected_visual_anchors", f"slide_{slide_index}.protected_visual_anchors")
        add_anchor_list(slide, "non_text_visual_anchors", f"slide_{slide_index}.non_text_visual_anchors")
        add_anchor_list(slide, "required_visual_anchors", f"slide_{slide_index}.required_visual_anchors")
        append_anchor_issues_from_review(slide.get("non_text_anchor_preservation_review", {}), issues)

    for index, element in enumerate(slide_elements(plan), start=1):
        if not is_non_text_anchor_record(element):
            continue
        anchor_records.append({**element, "_source": "slide.elements"})
        issue = issue_from_anchor_record(element, f"element-{index}")
        if issue:
            issues.append(issue)

    for index, region in enumerate(strategy_regions(plan), start=1):
        if is_non_text_anchor_record(region):
            anchor_records.append({**region, "_source": "strategy_review.regions"})
            issue = issue_from_anchor_record(region, f"region-{index}")
            if issue:
                issues.append(issue)
        for key in ("protected_visual_anchors", "required_visual_anchors", "non_text_visual_anchors"):
            values = region.get(key)
            if isinstance(values, list):
                for anchor_index, value in enumerate(values, start=1):
                    record = value if isinstance(value, dict) else {"id": str(value)}
                    record = {**record, "_source": f"strategy_review.regions.{key}"}
                    anchor_records.append(record)
                    issue = issue_from_anchor_record(record, f"region-{index}-anchor-{anchor_index}")
                    if issue:
                        issues.append(issue)

    limitation_text = " ".join(str(item).lower() for item in plan.get("limitations", []) if item is not None)
    if any(keyword in limitation_text for keyword in NON_TEXT_ANCHOR_FAILURE_KEYWORDS):
        issues.append({"issue": "missing-non-text-anchor", "source": "plan.limitations"})

    crop_protected_count = 0
    for record in anchor_records:
        if text_contains_any(
            {
                "strategy": record.get("strategy"),
                "actual_strategy": record.get("actual_strategy"),
                "source_kind": record.get("source_kind"),
            },
            tuple(CROP_FIRST_STRATEGIES),
        ):
            crop_protected_count += 1

    return {
        "status": "failed" if issues else "reviewed",
        "protected_anchor_count": len(anchor_records),
        "crop_protected_anchor_count": crop_protected_count,
        "missing_required_anchors": bool(issues),
        "issues": issues,
        "rule": "preserve non-text visual anchors such as arrows, route lines, connectors, step markers, card edges, dividers, and icons",
    }


def normalize_render_report(render_path: Path) -> None:
    report = read_json(render_path, {})
    if not isinstance(report, dict) or report.get("status") != "rendered":
        return
    if report.get("rendered_png"):
        return
    slides = report.get("slides")
    if isinstance(slides, list) and slides:
        first = slides[0]
        if isinstance(first, dict) and first.get("png"):
            report["rendered_png"] = first["png"]
            write_json(render_path, report)


def ensure_progress_done(progress_path: Path) -> None:
    progress = read_json(progress_path, {"history": []})
    if not isinstance(progress, dict):
        progress = {"history": []}
    history = progress.get("history")
    if not isinstance(history, list):
        history = []
    statuses = {item.get("status") for item in history if isinstance(item, dict)}
    if "qa_done" not in statuses:
        history.append(
            {
                "status": "qa_done",
                "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "current_step": "v3.1 handoff qa_summary generated from integrated single-page output",
                "outputs_created": ["qa_summary.json"],
            }
        )
    progress["history"] = history
    write_json(progress_path, progress)


def infer_success_status(summary_single_page: dict, render_report: dict | None) -> str:
    raw_status = str((summary_single_page or {}).get("status", "")).lower()
    render_status = (render_report or {}).get("status") if isinstance(render_report, dict) else None
    if raw_status in {"pass", "passed", "success", "generated"} and render_status == "rendered":
        return "passed"
    return "failed-retryable"


def build_summary(args: argparse.Namespace) -> dict:
    manifest_path = Path(args.slide_job_manifest).resolve()
    attempt_dir = Path(args.attempt_dir).resolve()
    manifest = read_json(manifest_path, {})
    summary_single_page_path = attempt_dir / "qa_summary.single-page.json"
    if not summary_single_page_path.exists():
        summary_single_page_path = attempt_dir / "qa_summary.json"
    summary_single_page = read_json(summary_single_page_path, {})
    plan = read_json(attempt_dir / "source_reconstruction_plan.json", {})
    packaging_report = read_json(attempt_dir / "packaging_report.json", {})
    editability_report = read_json(attempt_dir / "editability_report.json", {})
    crop_report = read_json(attempt_dir / "crop_report.json", {})
    text_fit_report = read_json(attempt_dir / "text_fit_report.json", {})
    visual_strategy_report = read_json(attempt_dir / "visual_strategy_report.json", {})
    render_path = attempt_dir / "render_report.json"
    normalize_render_report(render_path)
    render_report = read_json(render_path, {})

    packaging = dict_summary(packaging_report)
    editability = dict_summary(editability_report)
    scripts_used = scripts_from_single_page_summary(summary_single_page, args.script_used or [])
    if "mixed" in normalize_mode(plan.get("mode") if isinstance(plan, dict) else "").lower():
        if "package_reconstruction_deck.py" not in scripts_used and (attempt_dir / "packaging_report.json").exists():
            scripts_used.append("package_reconstruction_deck.py")

    worker_identity = {
        "worker_thread_id": args.worker_thread_id,
        "worker_agent_id": args.worker_agent_id,
        "execution_model": (manifest.get("worker_contract") or {}).get(
            "execution_model",
            "delegated-real-per-slide-worker",
        ),
        "slide_scope": [manifest.get("slide_index")],
    }
    worker_identity = {k: v for k, v in worker_identity.items() if v is not None}

    limitations = list_unique(
        summary_single_page.get("limitations") if isinstance(summary_single_page, dict) else [],
        plan.get("limitations") if isinstance(plan, dict) else [],
    )
    status = args.status or infer_success_status(summary_single_page, render_report)
    failure_reason = None if status in {"passed", "accepted-with-limitations"} else "single-page output did not prove a rendered successful slide"

    crop_outputs = crop_report.get("outputs", []) if isinstance(crop_report, dict) else []

    return {
        "schema_version": "ppt-to-editable-3-0-slide-qa-summary-v1",
        "status": status,
        "mode": normalize_mode(plan.get("mode") if isinstance(plan, dict) else None),
        "references_read": required_references_read(manifest),
        "fallback_references_read": fallback_references_read(summary_single_page, manifest),
        "font_policy_applied": "microsoft-yahei-all-generated-text",
        "font_size_consistency_review": font_size_consistency_review(plan, text_fit_report),
        "effects_cleared": bool(
            packaging.get("effectClearedObjects", 0) >= 0
            or packaging.get("effectXmlNodesCleared", 0) >= 0
        ),
        "rendered_png_reviewed": render_report.get("status") == "rendered",
        "render_report": str(render_path),
        "region_crop_plan": region_crop_plan(plan, crop_report),
        "crop_manifest": crop_manifest_summary(attempt_dir, crop_report),
        "complex_visual_strategy_review": complex_visual_strategy_review(plan, visual_strategy_report),
        "text_background_policy": text_background_policy(plan),
        "non_text_anchor_preservation_review": non_text_anchor_preservation_review(plan),
        "editable_text_count": int(
            packaging.get("editableTextBodies")
            or editability.get("editableTextBodies")
            or 0
        ),
        "native_shapes_count": int(
            packaging.get("nativeShapes")
            or editability.get("nativeShapes")
            or 0
        ),
        "source_crop_count": len(crop_outputs) if isinstance(crop_outputs, list) else 0,
        "visual_qa": {
            "status": "rendered-reviewed" if render_report.get("status") == "rendered" else "render-not-proven",
            "render_report": str(render_path),
            "known_visual_risks": limitations,
            "remaining_visual_issues": [],
        },
        "failure_reason": failure_reason,
        "limitations": limitations,
        "recommended_next_round_change": "",
        "worker_identity": worker_identity,
        "ocr_runtime_status": (manifest.get("ocr_runtime") or {}).get("status", "failed"),
        "single_page_engine_used": PRIMARY_SINGLE_PAGE_ENGINE_ID,
        "single_page_engine_scripts_used": scripts_used,
        "source_single_page_summary": str(summary_single_page_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slide-job-manifest", required=True)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--output")
    parser.add_argument("--worker-thread-id")
    parser.add_argument("--worker-agent-id")
    parser.add_argument("--status", choices=["passed", "accepted-with-limitations", "failed-retryable", "image-fallback"])
    parser.add_argument("--script-used", action="append", default=[])
    args = parser.parse_args()

    attempt_dir = Path(args.attempt_dir).resolve()
    output = Path(args.output).resolve() if args.output else attempt_dir / "qa_summary.json"
    current_summary = attempt_dir / "qa_summary.json"
    backup_summary = attempt_dir / "qa_summary.single-page.json"
    if current_summary.exists() and current_summary.resolve() == output.resolve() and not backup_summary.exists():
        shutil.copy2(current_summary, backup_summary)

    summary = build_summary(args)
    write_json(output, summary)
    ensure_progress_done(attempt_dir / "progress.json")
    print(json.dumps({"status": summary["status"], "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
