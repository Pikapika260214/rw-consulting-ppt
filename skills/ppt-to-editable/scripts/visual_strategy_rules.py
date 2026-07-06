"""Shared visual strategy rules for ppt-to-editable reconstruction QA."""

from __future__ import annotations

from typing import Any


HIGH_RISK_VISUAL_TYPES = {
    "curved_connector",
    "curved_connector_side_module",
    "thick_stepped_connector",
    "bracket_arrow",
    "side_path_module",
    "side_funnel_module",
    "icon_connected_navigation_path",
    "complex_process_card_group",
    "bridge_risk_module",
    "grouped_icon_card_connector_system",
    "product_photo_or_detailed_icon_group",
    "gradient_arrow_or_textured_band",
    "layered_card_stack",
    "complex_table_or_flow_matrix",
    "complex_matrix_background",
    "source_specific_process_matrix",
}

CROP_FIRST_STRATEGIES = {
    "source_textless_crop",
    "local_textless_crop",
    "textless_crop",
    "source_crop",
    "source_icon_crop",
    "tight_source_crop",
    "clean_badge_composite",
    "textless_crop_plus_editable_text",
}

TEXTLESS_STRATEGIES = {
    "source_textless_crop",
    "local_textless_crop",
    "textless_crop",
    "textless_crop_plus_editable_text",
}

SOURCE_CROP_STRATEGIES = CROP_FIRST_STRATEGIES

NATIVE_STRATEGIES = {
    "native_redraw",
    "native_lines",
    "native_shapes",
    "native_reconstruction",
    "manual_native_shape",
    "manual_native_line",
}

NOT_REPORTED_STRATEGIES = {"", "none", "null", "not-reported", "not_reported"}

FULL_SLIDE_PICTURE_HINTS = (
    "full_slide",
    "full-slide",
    "whole_slide",
    "whole-slide",
    "clean_textless_background",
    "textless_background_full_slide",
)


def normalized(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def is_high_risk_visual_type(value: Any) -> bool:
    return normalized(value) in HIGH_RISK_VISUAL_TYPES


def is_native_strategy(value: Any) -> bool:
    return normalized(value) in NATIVE_STRATEGIES


def is_crop_first_strategy(value: Any) -> bool:
    return normalized(value) in CROP_FIRST_STRATEGIES


def is_not_reported_strategy(value: Any) -> bool:
    return normalized(value) in NOT_REPORTED_STRATEGIES


def strategy_regions(plan: dict[str, Any]) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    review = plan.get("strategy_review")
    if isinstance(review, dict):
        for region in review.get("regions", []) or []:
            if isinstance(region, dict):
                regions.append(region)
    for slide_index, slide in enumerate(plan.get("slides", []) if isinstance(plan, dict) else [], start=1):
        if not isinstance(slide, dict):
            continue
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


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_float(record: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in record:
            value = as_float(record.get(key))
            if value is not None:
                return value
    return None


def element_text_blob(element: dict[str, Any]) -> str:
    source = element.get("source") if isinstance(element.get("source"), dict) else {}
    parts = [
        element.get("id"),
        element.get("role"),
        element.get("name"),
        element.get("description"),
        source.get("kind"),
        source.get("path"),
        source.get("role"),
    ]
    return " ".join(normalized(part) for part in parts if part is not None)


def is_full_slide_picture_hint(element: dict[str, Any]) -> bool:
    text = element_text_blob(element)
    return any(hint in text for hint in FULL_SLIDE_PICTURE_HINTS)


def slide_size(plan: dict[str, Any], slide: dict[str, Any]) -> tuple[float | None, float | None]:
    width = first_float(slide, ("slide_width_in", "width_in", "slide_width", "width"))
    height = first_float(slide, ("slide_height_in", "height_in", "slide_height", "height"))
    if width is None:
        width = first_float(plan, ("slide_width_in", "width_in", "slide_width", "width"))
    if height is None:
        height = first_float(plan, ("slide_height_in", "height_in", "slide_height", "height"))
    return width, height


def element_box(element: dict[str, Any]) -> tuple[float | None, float | None, float | None, float | None]:
    x = first_float(element, ("x", "left"))
    y = first_float(element, ("y", "top"))
    w = first_float(element, ("w", "width"))
    h = first_float(element, ("h", "height"))
    return x, y, w, h


def slide_elements_with_context(plan: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    elements: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for slide in plan.get("slides", []) if isinstance(plan, dict) else []:
        if not isinstance(slide, dict):
            continue
        for element in slide.get("elements", []) or []:
            if isinstance(element, dict):
                elements.append((element, slide))
    return elements


def full_slide_picture_ids(plan: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for element, slide in slide_elements_with_context(plan):
        if normalized(element.get("type")) != "picture":
            continue
        element_id = element.get("id")
        if element_id is None:
            continue
        if is_full_slide_picture_hint(element):
            ids.add(str(element_id))
            continue
        slide_w, slide_h = slide_size(plan, slide)
        x, y, w, h = element_box(element)
        if None in (slide_w, slide_h, x, y, w, h):
            continue
        assert slide_w is not None and slide_h is not None and x is not None and y is not None and w is not None and h is not None
        if slide_w <= 0 or slide_h <= 0:
            continue
        near_origin = x <= slide_w * 0.06 and y <= slide_h * 0.06
        near_full_size = w >= slide_w * 0.92 and h >= slide_h * 0.92
        if near_origin and near_full_size:
            ids.add(str(element_id))
    return ids


def plan_mode(plan: dict[str, Any], qa_summary: dict[str, Any] | None = None) -> str:
    if qa_summary and qa_summary.get("mode"):
        return normalized(qa_summary.get("mode"))
    return normalized(plan.get("mode"))


def full_slide_textless_background_issue(
    plan: dict[str, Any],
    packaging_summary: dict[str, Any] | None = None,
    qa_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Detect a fake mixed-reconstruction route backed by one whole-slide picture.

    A real crop-first plan should have bounded source/textless crop elements for
    its semantic regions. One near-full-slide picture cannot satisfy a 3-5 region
    crop plan unless the slide is explicitly accepted as image fallback.
    """
    if "reconstruction" not in plan_mode(plan, qa_summary):
        return None

    full_picture_ids = full_slide_picture_ids(plan)
    if not full_picture_ids:
        return None

    regions = [
        region
        for region in strategy_regions(plan)
        if (
            is_high_risk_visual_type(region.get("visual_type"))
            or is_crop_first_strategy(region.get("expected_strategy"))
            or is_crop_first_strategy(region.get("actual_strategy"))
        )
    ]
    if len(regions) < 2:
        return None

    disguised_regions: list[str] = []
    for region in regions:
        evidence_ids = set(as_list(region.get("evidence_element_ids")))
        if evidence_ids and evidence_ids.issubset(full_picture_ids):
            disguised_regions.append(str(region.get("id") or "strategy-region"))

    if len(disguised_regions) < max(2, int(len(regions) * 0.6)):
        return None

    packaging_summary = packaging_summary or {}
    pictures = as_int(packaging_summary.get("pictures"))
    cropped = as_int(packaging_summary.get("croppedPictures"))
    native_visuals = (
        as_int(packaging_summary.get("nativeShapes"))
        + as_int(packaging_summary.get("nativeLines"))
        + as_int(packaging_summary.get("nativeTables"))
    )
    reported_source_crops = as_int((qa_summary or {}).get("source_crop_count"))
    has_packaging_summary = bool(packaging_summary)
    if has_packaging_summary:
        only_whole_slide_visual_layer = pictures <= max(1, len(full_picture_ids)) and cropped == 0
        reported_crops_contradict_packaging = reported_source_crops >= 2 and pictures <= max(1, len(full_picture_ids))
        if not only_whole_slide_visual_layer and not reported_crops_contradict_packaging:
            return None
    else:
        only_whole_slide_visual_layer = True

    return {
        "issue": "full_slide_textless_background_disguised_as_region_crops",
        "full_slide_picture_ids": sorted(full_picture_ids),
        "region_count": len(regions),
        "disguised_region_count": len(disguised_regions),
        "disguised_region_ids": disguised_regions,
        "pictures": pictures,
        "croppedPictures": cropped,
        "nativeVisualObjects": native_visuals,
        "source_crop_count": reported_source_crops,
        "only_whole_slide_visual_layer": only_whole_slide_visual_layer,
    }


def high_risk_native_strategy_issues(plan: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for region in strategy_regions(plan):
        visual_type = region.get("visual_type")
        actual = region.get("actual_strategy")
        expected = region.get("expected_strategy")
        if not is_high_risk_visual_type(visual_type):
            continue
        if is_native_strategy(actual) or is_native_strategy(expected):
            issues.append(
                {
                    "issue": "high_risk_native_strategy",
                    "region_id": region.get("id"),
                    "visual_type": visual_type,
                    "expected_strategy": expected,
                    "actual_strategy": actual,
                }
            )
    return issues


def region_crop_plan_issues(region_plan: Any) -> list[dict[str, Any]]:
    if not isinstance(region_plan, list):
        return [{"issue": "region_crop_plan_missing"}]
    issues: list[dict[str, Any]] = []
    for index, region in enumerate(region_plan, start=1):
        if not isinstance(region, dict):
            issues.append({"issue": "region_crop_plan_invalid_entry", "index": index})
            continue
        strategy = region.get("strategy")
        if is_not_reported_strategy(strategy):
            issues.append({"issue": "region_crop_plan_not_reported", "region_id": region.get("id"), "index": index})
        if not region.get("source_bbox_px"):
            issues.append({"issue": "region_crop_plan_missing_source_bbox_px", "region_id": region.get("id"), "index": index})
        if not region.get("reason"):
            issues.append({"issue": "region_crop_plan_missing_reason", "region_id": region.get("id"), "index": index})
    return issues


def zero_crop_high_native_issue(plan: dict[str, Any], packaging_summary: dict[str, Any]) -> dict[str, Any] | None:
    if not high_risk_native_strategy_issues(plan):
        high_risk_regions = [region for region in strategy_regions(plan) if is_high_risk_visual_type(region.get("visual_type"))]
    else:
        high_risk_regions = [issue for issue in high_risk_native_strategy_issues(plan)]
    if not high_risk_regions:
        return None
    pictures = int(packaging_summary.get("pictures") or 0)
    cropped = int(packaging_summary.get("croppedPictures") or 0)
    native_shapes = int(packaging_summary.get("nativeShapes") or 0)
    native_lines = int(packaging_summary.get("nativeLines") or 0)
    if pictures == 0 and cropped == 0 and (native_shapes + native_lines) >= 20:
        return {
            "issue": "high_risk_zero_source_crops_all_native",
            "pictures": pictures,
            "croppedPictures": cropped,
            "nativeShapes": native_shapes,
            "nativeLines": native_lines,
        }
    return None
