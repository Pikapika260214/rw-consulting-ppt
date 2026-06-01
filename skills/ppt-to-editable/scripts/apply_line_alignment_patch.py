#!/usr/bin/env python3
"""Apply judge_line_alignment patch suggestions to a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply line alignment judge patch suggestions.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("judge", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--patch-log", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    judge = json.loads(args.judge.read_text(encoding="utf-8-sig"))
    patches = {
        str(item["patch"].get("name")): item["patch"]
        for item in judge.get("details", [])
        if item.get("patch")
    }
    applied: list[dict[str, Any]] = []
    for slide in manifest.get("slides", []):
        for box in slide.get("text_boxes", []):
            name = str(box.get("name"))
            patch = patches.get(name)
            if not patch:
                continue
            before = {
                "x": box.get("x"),
                "y": box.get("y"),
                "font_size": box.get("font_size"),
                "character_spacing": box.get("character_spacing", 0),
            }
            if patch.get("x_delta"):
                box["x"] = round(float(box["x"]) + float(patch["x_delta"]), 3)
            if patch.get("y_delta"):
                box["y"] = round(float(box["y"]) + float(patch["y_delta"]), 3)
            if patch.get("font_size_multiplier") and float(patch["font_size_multiplier"]) != 1.0:
                box["font_size"] = round(float(box.get("font_size", 12)) * float(patch["font_size_multiplier"]), 1)
            if patch.get("character_spacing_delta"):
                box["character_spacing"] = round(float(box.get("character_spacing", 0)) + float(patch["character_spacing_delta"]), 3)
            after = {
                "x": box.get("x"),
                "y": box.get("y"),
                "font_size": box.get("font_size"),
                "character_spacing": box.get("character_spacing", 0),
            }
            if before != after:
                box["alignment_status"] = "judge-patched"
                applied.append({"name": name, "before": before, "after": after, "patch": patch})

    manifest["phase"] = "ppt-to-editable-line-judge-patched"
    manifest["notes"] = (
        str(manifest.get("notes", "")).rstrip()
        + f" Applied {len(applied)} line-alignment judge patches."
    ).strip()
    manifest["line_alignment_patch_summary"] = {
        "applied": len(applied),
        "judge_summary": judge.get("summary", {}),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.patch_log:
        args.patch_log.parent.mkdir(parents=True, exist_ok=True)
        args.patch_log.write_text(json.dumps({"applied": applied}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(f"applied={len(applied)}")


if __name__ == "__main__":
    main()
