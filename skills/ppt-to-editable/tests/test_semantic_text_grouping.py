import importlib.util
import unittest
from pathlib import Path


CHECKER_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "check_reconstruction_plan_text_fit.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


checker = load_module("check_reconstruction_plan_text_fit", CHECKER_PATH)


def text_element(element_id: str, *, y: float, text: str, **overrides):
    element = {
        "id": element_id,
        "type": "text",
        "x": 1.0,
        "y": y,
        "w": 2.5,
        "h": 0.18,
        "text": text,
        "font_size": 11,
        "font_face": "Microsoft YaHei",
        "color": "#333333",
        "bold": False,
        "italic": False,
        "align": "left",
        "margin": 0.01,
        "word_wrap": False,
        "semantic_block": False,
        "trace_level": "line",
        "source": {
            "kind": "manual_reviewed_text",
            "source_bbox_px": [120, int(y * 120), 360, int(y * 120 + 20)],
            "review_status": "corrected",
        },
    }
    element.update(overrides)
    return element


class SemanticTextGroupingTests(unittest.TestCase):
    def test_same_style_adjacent_body_lines_warn_when_split_into_line_boxes(self) -> None:
        plan = {
            "slides": [
                {
                    "elements": [
                        text_element("body-line-1", y=1.0, text="需要稳定的识别与显示能力，"),
                        text_element("body-line-2", y=1.23, text="对续航、散热和交互准确性要求更高。"),
                        text_element("body-line-3", y=1.46, text="当前仍处于验证与构建阶段。"),
                    ]
                }
            ]
        }

        report = checker.check_plan(plan)

        self.assertEqual(report["status"], "warnings")
        self.assertEqual(
            report["summary"]["warnings_by_type"].get("candidate_multiline_split"),
            1,
        )
        warning = next(item for item in report["warnings"] if item["warning"] == "candidate_multiline_split")
        self.assertEqual(warning["element_ids"], ["body-line-1", "body-line-2", "body-line-3"])

    def test_title_and_body_are_not_forced_into_one_text_box(self) -> None:
        plan = {
            "slides": [
                {
                    "elements": [
                        text_element("card-title", y=1.0, text="眼前提示", font_size=16, bold=True),
                        text_element("card-body-1", y=1.34, text="翻译 / 导航 / 提问", font_size=11),
                    ]
                }
            ]
        }

        report = checker.check_plan(plan)

        self.assertNotIn("candidate_multiline_split", report["summary"]["warnings_by_type"])

    def test_short_icon_or_legend_labels_are_not_forced_into_one_text_box(self) -> None:
        plan = {
            "slides": [
                {
                    "elements": [
                        text_element("legend-label-1", y=1.0, text="计划跟踪更优", w=1.2),
                        text_element("legend-label-2", y=1.23, text="考核风险降低", w=1.2),
                    ]
                }
            ]
        }

        report = checker.check_plan(plan)

        self.assertNotIn("candidate_multiline_split", report["summary"]["warnings_by_type"])


if __name__ == "__main__":
    unittest.main()
