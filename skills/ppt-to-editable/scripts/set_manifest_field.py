#!/usr/bin/env python3
"""Set a field on every text box in a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Set a field on every manifest text box.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--field", required=True)
    parser.add_argument("--value", required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    value = parse_value(args.value)
    for slide in manifest.get("slides", []):
        for box in slide.get("text_boxes", []):
            box[args.field] = value
    if args.note:
        manifest["notes"] = (str(manifest.get("notes", "")).rstrip() + " " + args.note).strip()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
