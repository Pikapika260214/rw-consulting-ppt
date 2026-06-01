#!/usr/bin/env python3
"""Apply conservative role-specific text presets to an editable text manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CHINESE_LINE_TRACE: dict[str, dict[str, Any]] = {
    "title": {"font_size": 29.0, "line_spacing": 1.0},
    "subtitle": {"font_size": 13.5, "line_spacing": 1.0},
    "section": {"font_size": 15.0, "line_spacing": 1.0},
    "gate-number": {"font_size": 14.0, "line_spacing": 1.0},
    "gate-label": {"font_size": 11.0, "line_spacing": 1.0},
    "evidence-header": {"font_size": 11.2, "line_spacing": 1.0},
    "evidence-body": {"font_size": 10.6, "line_spacing": 1.14},
    "panel-title": {"font_size": 17.0, "line_spacing": 1.0},
    "panel-copy": {"font_size": 10.6, "line_spacing": 1.12},
    "line-item": {"font_size": 10.8, "line_spacing": 1.0},
    "takeaway": {"font_size": 17.5, "line_spacing": 1.0},
    "source": {"font_size": 7.0, "line_spacing": 1.0},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply role-specific text presets to a manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + " Applies Chinese line-trace role presets for stable alignment."
    ).strip()
    manifest["phase"] = "ppt-to-editable-role-presets"
    manifest["route"] = "clean-background-line-trace"

    for slide in manifest.get("slides", []):
        for box in slide.get("text_boxes", []):
            role = str(box.get("role", ""))
            preset = CHINESE_LINE_TRACE.get(role)
            if preset:
                box.update(preset)
            box.setdefault("alignment_status", "calibrated")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
