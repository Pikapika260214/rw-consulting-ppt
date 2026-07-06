import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
CONTROLLER_PATH = SCRIPTS_DIR / "deck_controller.py"
SUMMARY_SCRIPT = SCRIPTS_DIR / "write_slide_qa_summary_from_single_page.py"

spec = importlib.util.spec_from_file_location("deck_controller", CONTROLLER_PATH)
deck_controller = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(deck_controller)

TMP_ROOT = Path(tempfile.gettempdir()) / "ppt_to_editable_3_0_summary_tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def fresh_dir(name: str) -> Path:
    path = TMP_ROOT / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def as_relative_if_possible(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


class SlideQaSummaryFromSinglePageTests(unittest.TestCase):
    def test_single_page_outputs_are_closed_into_controller_accepted_3_0_summary(self) -> None:
        run_dir = fresh_dir("summary-bridge-run")
        source = run_dir / "source.png"
        source.write_bytes(b"placeholder")
        manifest = deck_controller.make_slide_job_manifest(
            "run-1",
            {
                "slide_index": 1,
                "pictures": [
                    {
                        "extracted_path": str(source),
                        "image_size": {"width_px": 1600, "height_px": 900},
                    }
                ],
            },
            run_dir,
            ocr_runtime_status="passed-text-usable",
        )
        slide_dir = run_dir / "slide_jobs" / "slide_01"
        attempt_dir = slide_dir / "attempt_01"
        rendered_png = attempt_dir / "render" / "slide_01.png"
        rendered_png.parent.mkdir(parents=True, exist_ok=True)
        rendered_png.write_bytes(b"png")
        (attempt_dir / "slide.pptx").write_bytes(b"placeholder")
        (attempt_dir / "visual-qa-comparison.html").write_text("<html></html>", encoding="utf-8")

        write_json(
            attempt_dir / "progress.json",
            {
                "history": [
                    {"status": "started"},
                    {"status": "ocr_done"},
                    {"status": "plan_done"},
                    {"status": "packaging_done"},
                ]
            },
        )
        write_json(
            attempt_dir / "source_reconstruction_plan.json",
            {
                "mode": "mixed_reconstruction",
                "limitations": ["Complex icons remain source crops."],
                "strategy_review": {
                    "regions": [
                        {
                            "id": "header",
                            "actual_strategy": "native_text",
                            "source_bbox_px": [60, 40, 1500, 130],
                            "reason": "Header text is rebuilt as editable text.",
                        },
                        {
                            "id": "body",
                            "actual_strategy": "source_crop",
                            "source_bbox_px": [70, 150, 1510, 760],
                            "reason": "Main visual uses source crops for fidelity.",
                        },
                        {
                            "id": "footer",
                            "actual_strategy": "native_text",
                            "source_bbox_px": [60, 780, 1500, 850],
                            "reason": "Footer text is rebuilt as editable text.",
                        },
                    ]
                },
            },
        )
        write_json(
            attempt_dir / "packaging_report.json",
            {
                "summary": {
                    "editableTextBodies": 12,
                    "nativeShapes": 7,
                    "pictures": 3,
                    "fullSlidePictures": 0,
                    "effectClearedObjects": 9,
                    "unwantedSplitTextBoxes": 0,
                }
            },
        )
        write_json(
            attempt_dir / "editability_report.json",
            {
                "summary": {
                    "editableTextBodies": 12,
                    "nativeShapes": 7,
                    "pictures": 3,
                    "fullSlidePictures": 0,
                }
            },
        )
        write_json(
            attempt_dir / "crop_report.json",
            {"outputs": [{"id": "icon-a"}, {"id": "icon-b"}, {"id": "icon-c"}]},
        )
        (attempt_dir / "render_report.json").write_text(
            json.dumps(
                {
                    "status": "rendered",
                    "slides": [{"index": 1, "png": str(rendered_png), "exists": True}],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8-sig",
        )
        write_json(
            attempt_dir / "qa_summary.json",
            {
                "status": "pass",
                "steps": [
                    {"name": "visual_strategy", "command": ["python", "check_reconstruction_visual_strategy.py"]},
                    {"name": "text_fit", "command": ["python", "check_reconstruction_plan_text_fit.py"]},
                    {"name": "package", "command": ["python", "package_reconstruction_deck.py"]},
                    {"name": "inspect_editability", "command": ["python", "inspect_pptx_editability.py"]},
                    {"name": "powerpoint_render", "command": ["powershell", "render_pptx_qa.ps1"]},
                ],
                "limitations": ["Complex icons remain source crops."],
                "artifacts": {"pptx": str(attempt_dir / "slide.pptx")},
            },
        )

        proc = subprocess.run(
            [
                sys.executable,
                str(SUMMARY_SCRIPT),
                "--slide-job-manifest",
                as_relative_if_possible(slide_dir / "slide_job_manifest.json"),
                "--attempt-dir",
                as_relative_if_possible(attempt_dir),
                "--worker-agent-id",
                "worker-123",
                "--output",
                as_relative_if_possible(attempt_dir / "qa_summary.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        result = deck_controller.collect_slide_result(
            {
                "slide_index": 1,
                "required_reading": manifest["required_reading"],
                "qa_summary_required_fields": manifest["qa_summary_required_fields"],
                "required_progress_statuses": deck_controller.REQUIRED_PROGRESS_STATUSES,
                "ocr_dependency_status_at_dispatch": "passed",
                "ocr_runtime_status_at_dispatch": "passed-text-usable",
            },
            run_dir,
        )

        self.assertEqual(result["status"], "passed", result.get("failure_reason"))
        summary = json.loads((attempt_dir / "qa_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["single_page_engine_used"], "ppt-to-editable-v3-1-preview")
        self.assertIn("worker_compact_protocol", {item["id"] for item in summary["references_read"]})
        self.assertEqual(summary["fallback_references_read"], [])
        self.assertTrue(summary["effects_cleared"])
        self.assertTrue(Path(summary["render_report"]).is_absolute())
        self.assertEqual(summary["worker_identity"]["worker_agent_id"], "worker-123")
        self.assertIn("qa_done", [item["status"] for item in json.loads((attempt_dir / "progress.json").read_text(encoding="utf-8"))["history"]])
        self.assertTrue((attempt_dir / "qa_summary.single-page.json").exists())


if __name__ == "__main__":
    unittest.main()
