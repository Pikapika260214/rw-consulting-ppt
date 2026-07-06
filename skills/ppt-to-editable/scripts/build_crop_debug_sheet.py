#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def load_report(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    records = []
    for item in data.get("outputs", []):
        output = item.get("output_path") or item.get("path")
        if not output:
            continue
        records.append(
            {
                "id": item.get("id", Path(output).stem),
                "path": str(Path(output)),
                "width": item.get("width"),
                "height": item.get("height"),
                "warnings": item.get("warnings", []),
            }
        )
    return records


def checkerboard(size: tuple[int, int], cell: int = 10) -> Image.Image:
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(235, 235, 235))
    return image


def write_sheet(records: list[dict[str, Any]], out_path: Path, cols: int) -> None:
    if not records:
        raise ValueError("no input images for debug sheet")
    cell_w = 160
    cell_h = 138
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, rec in enumerate(records):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        image = Image.open(rec["path"]).convert("RGBA")
        scale = min(96 / max(image.width, 1), 78 / max(image.height, 1), 2.0)
        resized = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
        preview = checkerboard(resized.size)
        preview = Image.alpha_composite(preview.convert("RGBA"), resized).convert("RGB")
        sheet.paste(preview, (x + (cell_w - resized.width) // 2, y + 8))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(220, 220, 220))
        draw.text((x + 6, y + 94), str(rec["id"])[:23], fill=(0, 0, 0))
        size_text = f"{image.width}x{image.height}"
        if rec.get("warnings"):
            size_text += " warn"
        draw.text((x + 6, y + 112), size_text, fill=(90, 90, 90))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a PNG debug sheet from crop outputs or a crop report.")
    parser.add_argument("--from-report", help="Read images from a crop/textless report JSON.")
    parser.add_argument("--inputs", nargs="*", help="Input PNG files.")
    parser.add_argument("--out", required=True, help="Output debug sheet PNG.")
    parser.add_argument("--cols", type=int, default=6, help="Number of columns.")
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    if args.from_report:
        records.extend(load_report(Path(args.from_report)))
    if args.inputs:
        records.extend({"id": Path(path).stem, "path": path} for path in args.inputs)
    write_sheet(records, Path(args.out), max(1, args.cols))
    print(json.dumps({"inputs": len(records), "out": str(Path(args.out).resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
