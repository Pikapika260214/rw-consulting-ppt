#!/usr/bin/env python3
"""Preflight text fit risks in a reconstruction plan before PPTX packaging."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LINE_LEVEL_ROLE_MARKERS = {
    "axis",
    "badge",
    "button",
    "caption",
    "cell",
    "chart",
    "coordinate",
    "icon",
    "label",
    "legend",
    "number",
    "pill",
    "step",
    "table",
    "tag",
    "tick",
}
SENTENCE_MARKERS = set("，。；：！？、,.!?;:")


ORPHAN_PUNCTUATION = set("，。！？；：、,.!?;:")


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def text_elements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    for slide_index, slide in enumerate(plan.get("slides", []), start=1):
        for element_index, element in enumerate(slide.get("elements", []), start=1):
            if element.get("type") == "text":
                copy = dict(element)
                copy["_slide_index"] = slide_index
                copy["_element_index"] = element_index
                elements.append(copy)
    return elements


def text_lines(element: dict[str, Any]) -> list[str]:
    return str(element.get("text", "")).splitlines() or [""]


def trace_level(element: dict[str, Any]) -> str:
    if element.get("trace_level"):
        return str(element["trace_level"]).strip().lower()
    return "paragraph" if as_bool(element.get("semantic_block"), True) else "line"


def normalized_color(value: Any) -> str:
    return str(value or "#111111").strip().lower().lstrip("#")


def normalized_font_face(value: Any) -> str:
    return str(value or "Microsoft YaHei").strip().lower()


def text_role(element: dict[str, Any]) -> str:
    source = element.get("source")
    values = [
        element.get("role"),
        element.get("text_role"),
        element.get("semantic_role"),
    ]
    if isinstance(source, dict):
        values.extend([source.get("role"), source.get("text_role"), source.get("semantic_role")])
    return " ".join(str(value).strip().lower() for value in values if value)


def line_level_required(element: dict[str, Any]) -> bool:
    source = element.get("source")
    if as_bool(element.get("line_level_trace_required"), False):
        return True
    if as_bool(element.get("do_not_merge"), False):
        return True
    if as_bool(element.get("preserve_line_level"), False):
        return True
    if isinstance(source, dict):
        if as_bool(source.get("line_level_trace_required"), False):
            return True
        if as_bool(source.get("do_not_merge"), False):
            return True
    role = text_role(element)
    return any(marker in role for marker in LINE_LEVEL_ROLE_MARKERS)


def style_signature(element: dict[str, Any]) -> tuple[Any, ...]:
    return (
        normalized_font_face(element.get("font_face")),
        round(float(element.get("font_size", 14)), 1),
        as_bool(element.get("bold"), False),
        as_bool(element.get("italic"), False),
        normalized_color(element.get("color")),
        str(element.get("align", "left")).strip().lower(),
    )


def is_line_trace_candidate(element: dict[str, Any]) -> bool:
    if trace_level(element) != "line":
        return False
    if as_bool(element.get("semantic_block"), False):
        return False
    if line_level_required(element):
        return False
    lines = text_lines(element)
    return len(lines) == 1 and bool(lines[0].strip())


def close_enough(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) <= tolerance


def same_column(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    prev_x = float(previous.get("x", 0))
    curr_x = float(current.get("x", 0))
    if not close_enough(prev_x, curr_x, 0.12):
        return False
    prev_w = float(previous.get("w", 0))
    curr_w = float(current.get("w", 0))
    if min(prev_w, curr_w) <= 0:
        return True
    return abs(prev_w - curr_w) <= max(0.35, min(prev_w, curr_w) * 0.35)


def vertical_continuation(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    prev_y = float(previous.get("y", 0))
    prev_h = float(previous.get("h", 0))
    curr_y = float(current.get("y", 0))
    if curr_y <= prev_y:
        return False
    gap = curr_y - (prev_y + prev_h)
    font_size = max(float(previous.get("font_size", 14)), float(current.get("font_size", 14)))
    max_gap = max(0.08, font_size * 1.15 / 72.0)
    return -0.03 <= gap <= max_gap


def text_length(text: str) -> int:
    return len(str(text).strip())


def has_sentence_marker(text: str) -> bool:
    return any(ch in SENTENCE_MARKERS for ch in str(text))


def paragraph_like_group(group: list[dict[str, Any]]) -> bool:
    """Reject compact label stacks unless they look like body/callout prose."""
    for element in group:
        text = str(element.get("text", "")).strip()
        width = float(element.get("w", 0))
        if text_length(text) >= 10:
            return True
        if has_sentence_marker(text):
            return True
        if width >= 1.8 and text_length(text) >= 6:
            return True
    return False


def candidate_split_groups(elements: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    by_slide: dict[int, list[dict[str, Any]]] = {}
    for element in elements:
        if is_line_trace_candidate(element):
            by_slide.setdefault(int(element.get("_slide_index", 1)), []).append(element)

    for slide_elements in by_slide.values():
        ordered = sorted(
            slide_elements,
            key=lambda item: (
                round(float(item.get("x", 0)), 2),
                float(item.get("y", 0)),
                int(item.get("_element_index", 0)),
            ),
        )
        current_group: list[dict[str, Any]] = []
        for element in ordered:
            if not current_group:
                current_group = [element]
                continue
            previous = current_group[-1]
            if (
                style_signature(previous) == style_signature(element)
                and same_column(previous, element)
                and vertical_continuation(previous, element)
            ):
                current_group.append(element)
                continue
            if len(current_group) >= 2 and paragraph_like_group(current_group):
                groups.append(current_group)
            current_group = [element]
        if len(current_group) >= 2 and paragraph_like_group(current_group):
            groups.append(current_group)
    return groups


def line_width_inches(line: str, font_size: float) -> float:
    width_units = sum(1.0 if ord(ch) > 127 else 0.55 for ch in line)
    return width_units * font_size * 0.58 / 72.0


def fit_reasons(element: dict[str, Any]) -> list[str]:
    font_size = float(element.get("font_size", 14))
    margin = float(element.get("margin", 0.03))
    box_w = max(float(element.get("w", 0)) - margin * 2, 0.01)
    box_h = max(float(element.get("h", 0)) - margin * 2, 0.01)
    lines = text_lines(element)
    needed_h = len(lines) * font_size * 1.18 / 72.0
    reasons: list[str] = []
    if needed_h > box_h:
        reasons.append("height")

    word_wrap = as_bool(element.get("word_wrap"), True)
    if as_bool(element.get("no_wrap"), False):
        word_wrap = False
    if not word_wrap:
        max_needed_w = max((line_width_inches(line, font_size) for line in lines), default=0.0)
        if max_needed_w > box_w:
            reasons.append("width_no_wrap")
    return reasons


def check_element(element: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    element_id = str(element.get("id", f"text-{element.get('_slide_index')}-{element.get('_element_index')}"))
    reasons = fit_reasons(element)
    if reasons:
        warnings.append(
            {
                "id": element_id,
                "warning": "text_overflow_risk",
                "reasons": reasons,
                "text_preview": str(element.get("text", ""))[:80],
            }
        )

    for line_no, line in enumerate(text_lines(element), start=1):
        stripped = line.strip()
        if stripped and stripped[0] in ORPHAN_PUNCTUATION:
            warnings.append(
                {
                    "id": element_id,
                    "warning": "punctuation_orphan_line",
                    "line": line_no,
                    "text_preview": stripped[:20],
                }
            )
        elif len(stripped) == 1 and ord(stripped) > 127:
            warnings.append(
                {
                    "id": element_id,
                    "warning": "single_character_line",
                    "line": line_no,
                    "text_preview": stripped,
                }
            )
    return warnings


def check_plan(plan: dict[str, Any]) -> dict[str, Any]:
    elements = text_elements(plan)
    warnings: list[dict[str, Any]] = []
    for element in elements:
        warnings.extend(check_element(element))
    for group in candidate_split_groups(elements):
        first = group[0]
        last = group[-1]
        warnings.append(
            {
                "id": str(first.get("id", "text")),
                "warning": "candidate_multiline_split",
                "element_ids": [str(element.get("id", "text")) for element in group],
                "text_preview": "\n".join(str(element.get("text", "")).strip() for element in group)[:160],
                "reason": (
                    "Adjacent line-level text boxes share font face, size, bold/italic, color, "
                    "alignment, column, and tight vertical spacing. Merge them into one semantic "
                    "text block unless line-level trace is intentionally required."
                ),
                "suggested_fix": {
                    "trace_level": "paragraph",
                    "semantic_block": True,
                    "text": "\n".join(str(element.get("text", "")).strip() for element in group),
                    "source_element_ids": [str(element.get("id", "text")) for element in group],
                },
                "bbox_in": [
                    min(float(element.get("x", 0)) for element in group),
                    min(float(element.get("y", 0)) for element in group),
                    max(float(element.get("x", 0)) + float(element.get("w", 0)) for element in group),
                    max(float(element.get("y", 0)) + float(element.get("h", 0)) for element in group),
                ],
                "slide_index": int(first.get("_slide_index", 1)),
                "element_range": [
                    int(first.get("_element_index", 0)),
                    int(last.get("_element_index", 0)),
                ],
            }
        )
    by_type: dict[str, int] = {}
    for warning in warnings:
        by_type[warning["warning"]] = by_type.get(warning["warning"], 0) + 1
    return {
        "tool": "check_reconstruction_plan_text_fit.py",
        "status": "warnings" if warnings else "pass",
        "summary": {
            "text_elements": len(elements),
            "warning_count": len(warnings),
            "warnings_by_type": by_type,
        },
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check reconstruction plan text fit risks.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = check_plan(load_plan(args.plan))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"]}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "pass" else 2)


if __name__ == "__main__":
    main()
