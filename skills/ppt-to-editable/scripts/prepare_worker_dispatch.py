#!/usr/bin/env python
"""Prepare a deterministic per-slide worker dispatch report.

This script intentionally does not launch workers. It reads the deck
controller's manifest, reports the Conversion Mode Gate, verifies the combined
Scope + Worker Gate, and writes a
local report that tells the controller Agent which slide jobs are ready and
whether external Codex worker execution is allowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPORT_SCHEMA_VERSION = "ppt-to-editable-worker-dispatch-report-v1"
WORKER_MODE_CHOICES = ("app-native", "external-codex", "manual")
RETIRED_WORKER_MODE_CHOICES = ("sequential",)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_manifest_path(run_dir: Path) -> Path:
    candidate = run_dir / "deck_manifest.json"
    if candidate.exists():
        return candidate
    if run_dir.name == "deck_manifest.json" and run_dir.exists():
        return run_dir
    raise FileNotFoundError(f"deck_manifest.json not found under {run_dir}")


def slide_prompt_records(manifest: dict) -> list[dict]:
    records = []
    for slide in manifest.get("slides", []):
        job_manifest = Path(slide.get("job_manifest", ""))
        agent_task = job_manifest.with_name("AGENT_TASK.md") if job_manifest.name else None
        records.append(
            {
                "slide_index": slide.get("slide_index"),
                "source_image": slide.get("source_image"),
                "job_manifest": str(job_manifest) if job_manifest.name else None,
                "agent_task": str(agent_task) if agent_task else None,
                "status": slide.get("status"),
            }
        )
    return records


def build_dispatch_report(run_dir: Path, worker_mode: str | None = None) -> dict:
    run_dir = run_dir.resolve()
    manifest_path = resolve_manifest_path(run_dir)
    manifest = read_json(manifest_path)
    gates = manifest.get("user_confirmation_gates") or {}
    conversion_gate = gates.get("conversion_mode_gate")
    conversion_mode = conversion_gate.get("user_choice") if isinstance(conversion_gate, dict) else None
    scope_worker_gate = gates.get("scope_and_worker_gate")
    recorded_mode = None
    if isinstance(scope_worker_gate, dict):
        recorded_mode = scope_worker_gate.get("worker_mode")
    requested_mode = worker_mode or recorded_mode or "manual"

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "ready",
        "run_dir": str(manifest_path.parent),
        "deck_manifest": str(manifest_path),
        "conversion_mode": conversion_mode,
        "worker_mode": requested_mode,
        "recorded_worker_mode": recorded_mode,
        "slide_count": manifest.get("slide_count"),
        "selected_slide_indices": manifest.get("selected_slide_indices", []),
        "worker_prompts": slide_prompt_records(manifest),
        "automatic_external_codex_allowed": False,
        "token_cost_note": (
            "Each selected slide is a separate worker task. Full-deck conversion costs "
            "more tokens than one sample page because the token cost scales with page count."
        ),
        "content_sharing_note": (
            "External Codex worker execution may send per-page task content and source slide "
            "paths to the worker runtime. It must be explicitly approved before use."
        ),
        "next_action": None,
        "issues": [],
    }

    if not isinstance(scope_worker_gate, dict):
        report["status"] = "blocked-worker-gate-missing"
        report["issues"].append(
            "deck_manifest.user_confirmation_gates.scope_and_worker_gate is missing."
        )
        report["next_action"] = "Run --probe, ask the combined scope + worker question, and recreate gates.json."
        return report

    if requested_mode in RETIRED_WORKER_MODE_CHOICES:
        report["status"] = "blocked-invalid-worker-mode"
        report["issues"].append(
            "worker_mode=sequential is retired and not supported in this release. "
            "Use app-native/manual per-slide workers for multi-agent-high-quality."
        )
        return report

    if requested_mode not in WORKER_MODE_CHOICES:
        report["status"] = "blocked-invalid-worker-mode"
        report["issues"].append(f"worker_mode must be one of {WORKER_MODE_CHOICES}; got {requested_mode!r}.")
        return report

    required_bools = [
        "worker_execution_approved",
        "token_cost_acknowledged",
        "content_sharing_acknowledged",
    ]
    missing = [field for field in required_bools if scope_worker_gate.get(field) is not True]
    if missing:
        report["status"] = "blocked-worker-approval-missing"
        report["issues"].append(
            "scope_and_worker_gate must set these fields to true: " + ", ".join(missing)
        )
        report["next_action"] = "Ask the combined scope + worker/token question and update gates.json."
        return report

    external_allowed = scope_worker_gate.get("external_codex_worker_approved") is True
    if requested_mode == "external-codex":
        if not external_allowed:
            report["status"] = "blocked-external-worker-not-approved"
            report["issues"].append(
                "External Codex worker execution was requested, but "
                "scope_and_worker_gate.external_codex_worker_approved is not true."
            )
            report["next_action"] = (
                "Do not launch codex exec. Use app-native/manual workers, or ask the user "
                "for explicit external Codex worker approval."
            )
            return report
        report["status"] = "ready-external-codex"
        report["automatic_external_codex_allowed"] = True
        report["next_action"] = "External Codex dispatch is allowed by gates.json; use the listed AGENT_TASK.md files."
        return report

    if requested_mode == "app-native":
        report["status"] = "ready-app-native"
        report["next_action"] = "Use app-native per-slide workers with the listed AGENT_TASK.md files."
        return report

    report["status"] = "manual-prompts-ready"
    report["next_action"] = "Open each listed AGENT_TASK.md in a clean worker context; do not use codex exec."
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare ppt-to-editable worker dispatch report")
    parser.add_argument("run_dir", type=Path, help="Run directory containing deck_manifest.json")
    parser.add_argument(
        "--worker-mode",
        choices=WORKER_MODE_CHOICES,
        default=None,
        help="Requested dispatch mode. Defaults to the mode recorded in gates.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Report path. Defaults to RUN_DIR/worker-dispatch-report.json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        report = build_dispatch_report(args.run_dir, args.worker_mode)
    except Exception as exc:  # noqa: BLE001 - CLI should return a structured error
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "error",
            "error": str(exc),
            "run_dir": str(args.run_dir),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    output = args.output or (args.run_dir / "worker-dispatch-report.json")
    write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
