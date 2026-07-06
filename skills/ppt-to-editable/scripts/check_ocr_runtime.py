#!/usr/bin/env python
"""Check whether the OCR runtime can recognize Chinese text.

The check is intentionally stronger than "can import RapidOCR":

- failed: OCR dependencies cannot run.
- passed-geometry-only: dependencies run, but Chinese sample text is not usable.
- passed-text-usable: Chinese sample text is recognized well enough to support reconstruction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


EXPECTED_TEXT = "可编辑转换测试"
OCR_TEXT_USABLE_STATUS = "passed-text-usable"
OCR_GEOMETRY_ONLY_STATUS = "passed-geometry-only"
OCR_FAILED_STATUS = "failed"


def add_dependency_paths(deps: Path | None) -> list[str]:
    added: list[str] = []
    if not deps:
        return added
    deps = deps.resolve()
    if not deps.exists():
        return added
    for rel in ("shapely.libs", "numpy.libs", os.path.join("onnxruntime", "capi")):
        path = deps / rel
        if path.is_dir():
            added.append(str(path))
            try:
                os.add_dll_directory(str(path))
            except Exception:
                pass
    sys.path.insert(0, str(deps))
    added.append(str(deps))
    return added


def import_checks() -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    for module in ("PIL.Image", "PIL.ImageDraw", "PIL.ImageFont", "shapely.geometry", "rapidocr_onnxruntime"):
        try:
            imported = __import__(module)
        except Exception as exc:  # noqa: BLE001 - diagnostic script should capture exact import failure
            checks[module] = {"status": "unavailable", "error": repr(exc)}
        else:
            checks[module] = {
                "status": "available",
                "error": None,
                "file": getattr(imported, "__file__", None),
            }
    return checks


def find_chinese_font() -> str | None:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def render_sample_image(output_dir: Path) -> tuple[Path | None, str | None]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # noqa: BLE001
        return None, f"pillow_unavailable: {exc!r}"

    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / "ocr-chinese-sample.png"
    font_path = find_chinese_font()
    if not font_path:
        return None, "chinese_font_not_found"
    font = ImageFont.truetype(font_path, 56)
    image = Image.new("RGB", (820, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.text((42, 54), EXPECTED_TEXT, fill=(0, 0, 0), font=font)
    image.save(image_path)
    return image_path, None


def extract_texts(value: Any) -> list[str]:
    texts: list[str] = []
    if value is None:
        return texts
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return texts
    if isinstance(value, dict):
        for key in ("text", "rec_text", "label", "transcription"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                texts.append(candidate)
        for item in value.values():
            texts.extend(extract_texts(item))
        return texts
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and isinstance(value[1], str):
            texts.append(value[1])
        for item in value:
            texts.extend(extract_texts(item))
    return texts


def run_ocr_sample(image_path: Path) -> tuple[list[str], str | None, float | None]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # noqa: BLE001
        return [], f"rapidocr_import_failed: {exc!r}", None
    started = time.perf_counter()
    try:
        engine = RapidOCR()
        raw_result = engine(str(image_path))
    except Exception as exc:  # noqa: BLE001
        return [], f"rapidocr_sample_failed: {exc!r}", None
    elapsed = time.perf_counter() - started
    return extract_texts(raw_result), None, elapsed


def classify_texts(texts: list[str]) -> tuple[str, dict[str, Any]]:
    joined = "".join(texts)
    matched_chars = sum(1 for char in set(EXPECTED_TEXT) if char in joined)
    if EXPECTED_TEXT in joined or matched_chars >= 4:
        return OCR_TEXT_USABLE_STATUS, {
            "expected_text": EXPECTED_TEXT,
            "recognized_texts": texts,
            "matched_expected_chars": matched_chars,
        }
    if texts:
        return OCR_GEOMETRY_ONLY_STATUS, {
            "expected_text": EXPECTED_TEXT,
            "recognized_texts": texts,
            "matched_expected_chars": matched_chars,
        }
    return OCR_GEOMETRY_ONLY_STATUS, {
        "expected_text": EXPECTED_TEXT,
        "recognized_texts": [],
        "matched_expected_chars": 0,
    }


def check_runtime(deps: Path | None, output_dir: Path | None) -> dict[str, Any]:
    output_dir = output_dir or (Path.cwd() / "ocr_runtime_check")
    added_paths = add_dependency_paths(deps)
    checks = import_checks()
    dependency_status = "passed" if all(item["status"] == "available" for item in checks.values()) else "warning"
    result: dict[str, Any] = {
        "schema_version": "ppt-to-editable-ocr-runtime-check-v1",
        "status": OCR_FAILED_STATUS,
        "ocr_runtime_status": OCR_FAILED_STATUS,
        "dependency_status": dependency_status,
        "runtime": {
            "python": sys.executable,
            "deps": str(deps.resolve()) if deps else None,
            "added_paths": added_paths,
        },
        "checks": checks,
        "sample": {
            "expected_text": EXPECTED_TEXT,
            "image_path": None,
            "recognized_texts": [],
            "elapsed_seconds": None,
            "error": None,
        },
    }
    if dependency_status != "passed":
        result["sample"]["error"] = "dependency_import_failed"
        return result

    image_path, render_error = render_sample_image(output_dir)
    if render_error or image_path is None:
        result["ocr_runtime_status"] = OCR_GEOMETRY_ONLY_STATUS
        result["status"] = OCR_GEOMETRY_ONLY_STATUS
        result["sample"]["error"] = render_error
        return result

    texts, ocr_error, elapsed = run_ocr_sample(image_path)
    result["sample"]["image_path"] = str(image_path)
    result["sample"]["recognized_texts"] = texts
    result["sample"]["elapsed_seconds"] = elapsed
    result["sample"]["error"] = ocr_error
    if ocr_error:
        result["ocr_runtime_status"] = OCR_GEOMETRY_ONLY_STATUS
        result["status"] = OCR_GEOMETRY_ONLY_STATUS
        return result

    status, sample_detail = classify_texts(texts)
    result["ocr_runtime_status"] = status
    result["status"] = status
    result["sample"].update(sample_detail)
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check OCR runtime Chinese text usability")
    parser.add_argument("--deps", type=Path, default=None, help="Optional site-packages dependency path")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for sample image and report")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = parse_args(argv)
    result = check_runtime(args.deps, args.output_dir)
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "ocr-runtime-check.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2 if not args.json else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
