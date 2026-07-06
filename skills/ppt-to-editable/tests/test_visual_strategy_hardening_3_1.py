import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
CHECKER_PATH = SCRIPTS_DIR / "check_reconstruction_visual_strategy.py"
CONTROLLER_PATH = SCRIPTS_DIR / "deck_controller.py"
SUMMARY_PATH = SCRIPTS_DIR / "write_slide_qa_summary_from_single_page.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


checker = load_module("check_reconstruction_visual_strategy", CHECKER_PATH)
deck_controller = load_module("deck_controller", CONTROLLER_PATH)
summary_bridge = load_module("write_slide_qa_summary_from_single_page", SUMMARY_PATH)

TMP_ROOT = Path(tempfile.gettempdir()) / "ppt_to_editable_3_1_visual_strategy_tests"
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


def valid_visual_reviews() -> dict:
    return {
        "font_size_consistency_review": {"status": "reviewed", "issues": []},
        "complex_visual_strategy_review": {
            "status": "reviewed",
            "unresolved_native_redraw_drift": False,
            "issues": [],
        },
        "text_background_policy": {
            "status": "reviewed",
            "invented_text_backgrounds_added": False,
            "issues": [],
        },
        "non_text_anchor_preservation_review": {
            "status": "reviewed",
            "missing_required_anchors": False,
            "issues": [],
        },
    }


class VisualStrategyHardening31Tests(unittest.TestCase):
    def test_high_risk_native_reconstruction_is_blocked_even_with_override_reason(self) -> None:
        plan = {
            "strategy_review": {
                "regions": [
                    {
                        "id": "main-process-module",
                        "visual_type": "complex_process_card_group",
                        "expected_strategy": "native_reconstruction",
                        "actual_strategy": "native_reconstruction",
                        "evidence_element_ids": ["native-line-1"],
                        "override_reason": "Manual native reconstruction is acceptable for this low-download single PNG run.",
                    }
                ]
            },
            "slides": [
                {
                    "elements": [
                        {"id": "native-line-1", "type": "line"},
                    ]
                }
            ],
        }

        report = checker.check_plan(plan, require_strategy_review=True)

        self.assertEqual(report["status"], "warnings")
        self.assertIn(
            "native_redraw_used_for_high_risk_region",
            report["summary"]["warnings_by_type"],
        )

    def test_gradient_arrow_and_matrix_types_are_high_risk(self) -> None:
        plan = {
            "strategy_review": {
                "regions": [
                    {
                        "id": "arrow-band",
                        "visual_type": "gradient_arrow_or_textured_band",
                        "expected_strategy": "source_textless_crop",
                        "actual_strategy": "native_lines",
                        "evidence_element_ids": ["line-1"],
                    },
                    {
                        "id": "flow-matrix",
                        "visual_type": "complex_table_or_flow_matrix",
                        "expected_strategy": "source_textless_crop",
                        "actual_strategy": "native_shapes",
                        "evidence_element_ids": ["shape-1"],
                    },
                ]
            },
            "slides": [
                {
                    "elements": [
                        {"id": "line-1", "type": "line"},
                        {"id": "shape-1", "type": "shape"},
                    ]
                }
            ],
        }

        report = checker.check_plan(plan, require_strategy_review=True)

        self.assertEqual(report["status"], "warnings")
        self.assertGreaterEqual(
            report["summary"]["warnings_by_type"].get("native_redraw_used_for_high_risk_region", 0),
            2,
        )

    def test_region_crop_plan_does_not_pad_missing_regions_with_not_reported(self) -> None:
        regions = summary_bridge.region_crop_plan({"mode": "mixed_reconstruction"}, None)

        self.assertEqual(regions, [])

    def test_controller_rejects_passed_slide_when_plan_has_high_risk_native_strategy_despite_passing_report(self) -> None:
        run_dir = fresh_dir("controller-plan-recheck")
        slide_dir = run_dir / "slide_jobs" / "slide_01"
        attempt_dir = slide_dir / "attempt_01"
        rendered_png = attempt_dir / "render" / "slide_01.png"
        rendered_png.parent.mkdir(parents=True, exist_ok=True)
        rendered_png.write_bytes(b"png")
        (attempt_dir / "slide.pptx").write_bytes(b"pptx")

        write_json(
            attempt_dir / "progress.json",
            {"history": [{"status": status} for status in deck_controller.REQUIRED_PROGRESS_STATUSES]},
        )
        write_json(
            attempt_dir / "render_report.json",
            {"status": "rendered", "rendered_png": "render/slide_01.png"},
        )
        write_json(
            attempt_dir / "source_reconstruction_plan.json",
            {
                "mode": "mixed_reconstruction",
                "strategy_review": {
                    "regions": [
                        {
                            "id": "main-process-module",
                            "visual_type": "complex_process_card_group",
                            "expected_strategy": "native_reconstruction",
                            "actual_strategy": "native_reconstruction",
                            "evidence_element_ids": ["native-line-1"],
                            "override_reason": "Manual native reconstruction is acceptable.",
                        }
                    ]
                },
                "slides": [{"elements": [{"id": "native-line-1", "type": "line"}]}],
            },
        )
        write_json(
            attempt_dir / "visual_strategy_report.json",
            {
                "tool": "check_reconstruction_visual_strategy.py",
                "status": "pass",
                "summary": {"regions": 1, "warning_count": 0, "warnings_by_type": {}},
                "warnings": [],
            },
        )
        write_json(
            attempt_dir / "packaging_report.json",
            {
                "summary": {
                    "pictures": 0,
                    "croppedPictures": 0,
                    "fullSlidePictures": 0,
                    "nativeShapes": 51,
                    "nativeLines": 52,
                    "editableTextBodies": 42,
                }
            },
        )
        write_json(
            attempt_dir / "qa_summary.json",
            {
                "schema_version": "ppt-to-editable-3-0-slide-qa-summary-v1",
                "status": "passed",
                "mode": "mixed-reconstruction",
                "references_read": [],
                "font_policy_applied": "microsoft-yahei-all-runs",
                "effects_cleared": True,
                "rendered_png_reviewed": True,
                "render_report": "render_report.json",
                "region_crop_plan": [
                    {
                        "id": "main-process-module",
                        "strategy": "native_reconstruction",
                        "source_bbox_px": [0, 100, 1600, 800],
                        "reason": "manual native reconstruction",
                    },
                    {
                        "id": "header",
                        "strategy": "native_text",
                        "source_bbox_px": [0, 0, 1600, 120],
                        "reason": "title text",
                    },
                    {
                        "id": "footer",
                        "strategy": "native_text",
                        "source_bbox_px": [0, 800, 1600, 900],
                        "reason": "footer text",
                    },
                ],
                **valid_visual_reviews(),
                "editable_text_count": 42,
                "native_shapes_count": 51,
                "source_crop_count": 0,
                "visual_qa": {"status": "rendered-reviewed", "remaining_visual_issues": []},
                "failure_reason": None,
                "limitations": [],
                "worker_identity": {
                    "worker_agent_id": "worker-1",
                    "execution_model": "delegated-real-per-slide-worker",
                    "slide_scope": [1],
                },
                "ocr_runtime_status": "passed-text-usable",
                "single_page_engine_used": "ppt-to-editable-v3-1-preview",
                "single_page_engine_scripts_used": ["package_reconstruction_deck.py"],
            },
        )

        result = deck_controller.collect_slide_result(
            {
                "slide_index": 1,
                "required_reading": [],
                "qa_summary_required_fields": [],
                "required_progress_statuses": deck_controller.REQUIRED_PROGRESS_STATUSES,
                "ocr_dependency_status_at_dispatch": "passed",
                "ocr_runtime_status_at_dispatch": "passed-text-usable",
            },
            run_dir,
        )

        self.assertEqual(result["status"], "failed-retryable")
        self.assertIn("high_risk_native", result["failure_reason"])

    def test_controller_rejects_full_slide_textless_background_disguised_as_region_crops(self) -> None:
        run_dir = fresh_dir("controller-full-slide-textless-recheck")
        slide_dir = run_dir / "slide_jobs" / "slide_01"
        attempt_dir = slide_dir / "attempt_01"
        rendered_png = attempt_dir / "render" / "slide_01.png"
        rendered_png.parent.mkdir(parents=True, exist_ok=True)
        rendered_png.write_bytes(b"png")
        (attempt_dir / "slide.pptx").write_bytes(b"pptx")

        write_json(
            attempt_dir / "progress.json",
            {"history": [{"status": status} for status in deck_controller.REQUIRED_PROGRESS_STATUSES]},
        )
        write_json(
            attempt_dir / "render_report.json",
            {"status": "rendered", "rendered_png": "render/slide_01.png"},
        )
        full_slide_picture = {
            "id": "textless_background_full_slide",
            "type": "picture",
            "role": "clean_textless_background",
            "x": 0,
            "y": 0,
            "w": 13.333333,
            "h": 7.5,
            "source": {"kind": "source_textless_crop"},
        }
        strategy_regions = [
            {
                "id": "left-process",
                "visual_type": "complex_table_or_flow_matrix",
                "expected_strategy": "source_textless_crop",
                "actual_strategy": "textless_crop_plus_editable_text",
                "evidence_element_ids": ["textless_background_full_slide"],
                "text_overlay_element_ids": ["left-text"],
                "source_bbox_px": [0, 120, 520, 760],
            },
            {
                "id": "center-process",
                "visual_type": "complex_process_card_group",
                "expected_strategy": "source_textless_crop",
                "actual_strategy": "textless_crop_plus_editable_text",
                "evidence_element_ids": ["textless_background_full_slide"],
                "text_overlay_element_ids": ["center-text"],
                "source_bbox_px": [520, 120, 1100, 760],
            },
            {
                "id": "right-process",
                "visual_type": "gradient_arrow_or_textured_band",
                "expected_strategy": "source_textless_crop",
                "actual_strategy": "textless_crop_plus_editable_text",
                "evidence_element_ids": ["textless_background_full_slide"],
                "text_overlay_element_ids": ["right-text"],
                "source_bbox_px": [1100, 120, 1600, 760],
            },
        ]
        write_json(
            attempt_dir / "source_reconstruction_plan.json",
            {
                "mode": "mixed_reconstruction",
                "slide_width_in": 13.333333,
                "slide_height_in": 7.5,
                "strategy_review": {"regions": strategy_regions},
                "slides": [
                    {
                        "elements": [
                            full_slide_picture,
                            {"id": "left-text", "type": "text"},
                            {"id": "center-text", "type": "text"},
                            {"id": "right-text", "type": "text"},
                        ]
                    }
                ],
            },
        )
        write_json(
            attempt_dir / "visual_strategy_report.json",
            {
                "tool": "check_reconstruction_visual_strategy.py",
                "status": "pass",
                "summary": {"regions": 3, "warning_count": 0, "warnings_by_type": {}},
                "warnings": [],
            },
        )
        write_json(
            attempt_dir / "packaging_report.json",
            {
                "summary": {
                    "pictures": 1,
                    "croppedPictures": 0,
                    "fullSlidePictures": 0,
                    "nativeShapes": 0,
                    "nativeLines": 0,
                    "nativeTables": 0,
                    "editableTextBodies": 32,
                }
            },
        )
        write_json(
            attempt_dir / "qa_summary.json",
            {
                "schema_version": "ppt-to-editable-3-0-slide-qa-summary-v1",
                "status": "accepted-with-limitations",
                "mode": "mixed-reconstruction",
                "references_read": [],
                "font_policy_applied": "microsoft-yahei-all-runs",
                "effects_cleared": True,
                "rendered_png_reviewed": True,
                "render_report": "render_report.json",
                "region_crop_plan": [
                    {
                        "id": "left-process",
                        "strategy": "textless_crop_plus_editable_text",
                        "source_bbox_px": [0, 120, 520, 760],
                        "reason": "left module should use local textless crop",
                    },
                    {
                        "id": "center-process",
                        "strategy": "textless_crop_plus_editable_text",
                        "source_bbox_px": [520, 120, 1100, 760],
                        "reason": "center module should use local textless crop",
                    },
                    {
                        "id": "right-process",
                        "strategy": "textless_crop_plus_editable_text",
                        "source_bbox_px": [1100, 120, 1600, 760],
                        "reason": "right module should use local textless crop",
                    },
                ],
                **valid_visual_reviews(),
                "editable_text_count": 32,
                "native_shapes_count": 0,
                "source_crop_count": 3,
                "visual_qa": {"status": "rendered-reviewed", "remaining_visual_issues": []},
                "failure_reason": None,
                "limitations": [],
                "worker_identity": {
                    "worker_agent_id": "worker-1",
                    "execution_model": "delegated-real-per-slide-worker",
                    "slide_scope": [1],
                },
                "ocr_runtime_status": "passed-text-usable",
                "single_page_engine_used": "ppt-to-editable-v3-1-preview",
                "single_page_engine_scripts_used": ["package_reconstruction_deck.py"],
            },
        )

        result = deck_controller.collect_slide_result(
            {
                "slide_index": 1,
                "required_reading": [],
                "qa_summary_required_fields": [],
                "required_progress_statuses": deck_controller.REQUIRED_PROGRESS_STATUSES,
                "ocr_dependency_status_at_dispatch": "passed",
                "ocr_runtime_status_at_dispatch": "passed-text-usable",
            },
            run_dir,
        )

        self.assertEqual(result["status"], "failed-retryable")
        self.assertIn("full_slide_textless", result["failure_reason"])


if __name__ == "__main__":
    unittest.main()
