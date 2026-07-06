#!/usr/bin/env python3
"""Check whether the OCR runtime can import its required local dependencies."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


DEFAULT_MODULES = [
    "rapidocr_onnxruntime",
    "onnxruntime",
    "numpy",
    "cv2",
    "PIL",
    "shapely",
    "shapely.geometry",
    "pyclipper",
    "yaml",
]


def add_local_deps(deps: Path | None) -> list[str]:
    added: list[str] = []
    if not deps:
        return added
    deps = deps.resolve()
    if not deps.exists():
        return added
    for subdir in ("shapely.libs", "numpy.libs", os.path.join("onnxruntime", "capi")):
        dll_dir = deps / subdir
        if dll_dir.exists() and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(dll_dir))
            added.append(str(dll_dir))
    sys.path.insert(0, str(deps))
    added.append(str(deps))
    return added


def module_version(module: Any) -> str | None:
    for attr in ("__version__", "VERSION", "version"):
        value = getattr(module, attr, None)
        if isinstance(value, str):
            return value
    return None


def check_import(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "available": True,
        "file": str(getattr(module, "__file__", "")),
        "version": module_version(module),
    }


def check_runtime(modules: list[str] | None = None, deps: Path | None = None) -> dict[str, Any]:
    modules = modules or DEFAULT_MODULES
    added_paths = add_local_deps(deps)
    imports = {module_name: check_import(module_name) for module_name in modules}
    missing = [name for name, result in imports.items() if not result["available"]]
    ready = not missing
    status: dict[str, Any] = {
        "ocr_ready": ready,
        "missing_modules": missing,
    }
    if not ready:
        status["recommended_action"] = (
            "Use a run-local OCR dependency folder, repair the OCR environment, "
            "or continue without OCR only as an explicitly labeled low-confidence run."
        )
    return {
        "tool": "preflight_ocr_runtime.py",
        "python": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "deps": str(deps.resolve()) if deps else None,
        "added_paths": added_paths,
        "imports": imports,
        "status": status,
    }


def parse_modules(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight RapidOCR runtime imports.")
    parser.add_argument("--deps", type=Path, default=Path(".deps/ppt-to-editable-ocr"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--modules", help="Comma-separated module override, mainly for tests.")
    args = parser.parse_args()

    report = check_runtime(modules=parse_modules(args.modules), deps=args.deps)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["status"], ensure_ascii=False))
    raise SystemExit(0 if report["status"]["ocr_ready"] else 2)


if __name__ == "__main__":
    main()
