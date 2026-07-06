#!/usr/bin/env python
"""Prepare a local OCR runtime for ppt-to-editable v3.1 preview.

This script is approval-gated by design. Without --yes it only prints the
user-facing explanation and exits without downloading or installing anything.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


DEFAULT_PACKAGES = [
    "rapidocr_onnxruntime==1.4.4",
    "onnxruntime",
    "pillow",
    "numpy<2",
]

GATES_SCHEMA_VERSION = "ppt-to-editable-gates-v3"

CONFIRMATION_MESSAGE = """我需要先配置 OCR Runtime。

OCR 用来识别 PPT 图片里的文字，并尽量把它们转成可编辑文本。
第一次配置会安装依赖并下载中文 OCR 模型，可能需要几分钟。
之后会缓存到本地，后续转换通常不需要重复下载。

是否现在继续？
"""


def runtime_python(runtime_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return runtime_dir / "Scripts" / "python.exe"
    return runtime_dir / "bin" / "python"


def load_and_validate_setup_gates(gates_file: Path | None) -> dict:
    if gates_file is None:
        raise ValueError(
            "--gates-file is required with --yes. Run deck_controller.py --probe first, "
            "ask the user to confirm OCR setup, record the answer in gates.json, then retry."
        )
    gates_file = gates_file.resolve()
    if not gates_file.exists():
        raise FileNotFoundError(f"Gates file not found: {gates_file}")
    gates = json.loads(gates_file.read_text(encoding="utf-8-sig"))
    if gates.get("schema_version") != GATES_SCHEMA_VERSION:
        raise ValueError(
            f"gates schema_version must be {GATES_SCHEMA_VERSION}; "
            f"got {gates.get('schema_version')!r}."
        )

    ocr_gate = gates.get("ocr_runtime_gate") or {}
    if ocr_gate.get("setup_required") is not True:
        raise ValueError(
            "OCR Runtime Gate violation: setup_ocr_runtime.py --yes requires "
            "ocr_runtime_gate.setup_required=true. If OCR is already passed-text-usable, "
            "record auto_passed_existing_runtime=true and do not run setup."
        )
    if ocr_gate.get("explained_to_user") is not True:
        raise ValueError(
            "OCR Runtime Gate violation: explain OCR and first-time setup cost to the user "
            "before running setup_ocr_runtime.py --yes."
        )
    if ocr_gate.get("user_confirmed_setup") is not True:
        raise ValueError(
            "OCR Runtime Gate violation: --yes requires "
            "ocr_runtime_gate.user_confirmed_setup=true in gates.json."
        )
    if not str(ocr_gate.get("user_response_quote") or "").strip():
        raise ValueError(
            "OCR Runtime Gate violation: record the user's actual confirmation in "
            "ocr_runtime_gate.user_response_quote."
        )
    return gates


def utf8_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Setup OCR runtime for ppt-to-editable v3.1 preview")
    parser.add_argument("--runtime-dir", type=Path, default=Path(".venv-ocr-3-0"))
    parser.add_argument("--yes", action="store_true", help="Confirmed by user; actually create/install runtime")
    parser.add_argument(
        "--gates-file",
        type=Path,
        default=None,
        help="JSON evidence that the user confirmed OCR setup after seeing the explanation.",
    )
    parser.add_argument("--package", action="append", default=[], help="Additional package spec")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = parse_args(argv)
    runtime_dir = args.runtime_dir.resolve()
    if not args.yes:
        result = {
            "status": "requires-user-confirmation",
            "runtime_dir": str(runtime_dir),
            "message": CONFIRMATION_MESSAGE,
            "next_command": f"{sys.executable} \"{Path(__file__).resolve()}\" --runtime-dir \"{runtime_dir}\" --gates-file GATES_FILE --yes",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else CONFIRMATION_MESSAGE)
        return 0

    try:
        gates = load_and_validate_setup_gates(args.gates_file)
    except Exception as exc:
        result = {
            "status": "gate-validation-failed",
            "error": str(exc),
            "gates_file": str(args.gates_file) if args.gates_file else None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    runtime_dir.parent.mkdir(parents=True, exist_ok=True)
    if not runtime_python(runtime_dir).exists():
        venv.EnvBuilder(with_pip=True, clear=False).create(runtime_dir)

    py = runtime_python(runtime_dir)
    packages = DEFAULT_PACKAGES + args.package
    install_cmd = [str(py), "-m", "pip", "install", *packages]
    install = subprocess.run(
        install_cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_subprocess_env(),
    )
    if install.returncode != 0:
        result = {
            "status": "install-failed",
            "runtime_dir": str(runtime_dir),
            "python": str(py),
            "packages": packages,
            "stderr": install.stderr,
            "stdout": install.stdout,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return install.returncode

    checker = Path(__file__).with_name("check_ocr_runtime.py")
    check = subprocess.run(
        [str(py), str(checker), "--json", "--output-dir", str(runtime_dir / "ocr-runtime-check")],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_subprocess_env(),
    )
    result = {
        "status": "setup-complete" if check.returncode == 0 else "setup-complete-check-failed",
        "runtime_dir": str(runtime_dir),
        "python": str(py),
        "packages": packages,
        "gates_schema_version": gates.get("schema_version"),
        "gates_file": str(args.gates_file.resolve()),
        "check_stdout": check.stdout,
        "check_stderr": check.stderr,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if check.returncode == 0 else check.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
