import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from PIL import Image


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "render_pptx_qa.py"
)
TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".test-tmp"


def fresh_dir(name: str) -> Path:
    path = TEST_TMP_ROOT / name
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


class RenderHelperContractTests(unittest.TestCase):
    def tearDown(self) -> None:
        if TEST_TMP_ROOT.exists():
            shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)

    def test_existing_rendered_png_produces_standard_report(self) -> None:
        run_dir = fresh_dir("render-helper")
        pptx = run_dir / "slide.pptx"
        pptx.write_bytes(b"placeholder")
        source = run_dir / "source.png"
        rendered = run_dir / "already-rendered.png"
        Image.new("RGB", (160, 90), "white").save(source)
        Image.new("RGB", (160, 90), "black").save(rendered)

        report_path = run_dir / "render_report.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(pptx),
                "--out-dir",
                str(run_dir / "render"),
                "--source",
                str(source),
                "--existing-rendered",
                str(rendered),
                "--report",
                str(report_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "rendered")
        self.assertEqual(report["renderer"], "existing-rendered-png")
        self.assertTrue(Path(report["rendered_png"]).exists())
        self.assertIn("diff_metrics", report)


if __name__ == "__main__":
    unittest.main()
