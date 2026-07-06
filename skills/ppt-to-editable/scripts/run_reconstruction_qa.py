#!/usr/bin/env python3
"""Run the standard reconstruction QA chain for a reviewed plan."""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


class StepFailed(RuntimeError):
    def __init__(self, name: str, command: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.name = name
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"{name} failed with exit code {returncode}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_uri()


def powershell_join_path_arg(path: Path) -> str:
    """render_pptx_qa.ps1 joins OutDir/Report with its cwd, so pass relative paths."""
    return os.path.relpath(path.resolve(), SCRIPT_DIR.resolve())


def run_step(name: str, command: list[str], *, allow_warning_exit: bool = False) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=SCRIPT_DIR, capture_output=True, text=True)
    allowed = {0}
    if allow_warning_exit:
        allowed.add(2)
    if completed.returncode not in allowed:
        raise StepFailed(name, command, completed.returncode, completed.stdout, completed.stderr)
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def python_cmd(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPT_DIR / script_name), *args]


def warning_count(report: dict[str, Any]) -> int:
    summary = report.get("summary")
    if isinstance(summary, dict):
        return int(summary.get("warning_count", 0))
    return 0


def make_html(
    html_path: Path,
    *,
    title: str,
    source_path: Path | None,
    render_image: Path | None,
    summary: dict[str, Any],
) -> None:
    source_html = (
        f'<img src="{html.escape(rel(source_path, html_path.parent))}" alt="source">'
        if source_path and source_path.exists()
        else '<div class="missing">No source image provided</div>'
    )
    render_html = (
        f'<img src="{html.escape(rel(render_image, html_path.parent))}" alt="rendered PPT">'
        if render_image and render_image.exists()
        else '<div class="missing">Render image not available in this QA run</div>'
    )
    metrics = {
        "fullSlidePictures": summary.get("packaging", {}).get("fullSlidePictures", "-"),
        "editableTextBodies": summary.get("packaging", {}).get("editableTextBodies", "-"),
        "nativeShapes": summary.get("packaging", {}).get("nativeShapes", "-"),
        "pictures": summary.get("packaging", {}).get("pictures", "-"),
        "warnings": summary.get("total_warning_count", "-"),
    }
    metric_html = "\n".join(
        f'<div class="metric"><strong>{html.escape(str(value))}</strong><span>{html.escape(key)}</span></div>'
        for key, value in metrics.items()
    )
    html_path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; color: #111827; background: #fff; }}
    header {{ padding: 22px 28px 16px; border-bottom: 1px solid #d7dde7; }}
    h1 {{ margin: 0 0 14px; font-size: 22px; line-height: 1.35; letter-spacing: 0; }}
    .summary {{ display: grid; grid-template-columns: repeat(5, minmax(140px, 1fr)); gap: 10px; }}
    .metric {{ border: 1px solid #d7dde7; border-radius: 6px; padding: 10px 12px; background: #f8fafc; }}
    .metric strong {{ display: block; color: #c40000; font-size: 18px; }}
    .metric span {{ display: block; margin-top: 4px; color: #64748b; font-size: 12px; }}
    main {{ padding: 18px 28px 28px; }}
    .compare {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; align-items: start; }}
    figure {{ margin: 0; border: 1px solid #d7dde7; border-radius: 6px; overflow: hidden; background: #fff; }}
    figcaption {{ padding: 10px 12px; border-bottom: 1px solid #d7dde7; font-size: 14px; font-weight: 700; }}
    img {{ display: block; width: 100%; height: auto; }}
    .missing {{ min-height: 220px; display: grid; place-items: center; color: #64748b; background: #f8fafc; }}
    @media (max-width: 1000px) {{ .summary, .compare {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <section class="summary">{metric_html}</section>
  </header>
  <main>
    <section class="compare">
      <figure><figcaption>Source image</figcaption>{source_html}</figure>
      <figure><figcaption>Rendered PPT</figcaption>{render_html}</figure>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_markdown_summary(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Reconstruction QA Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Total warnings: `{summary['total_warning_count']}`",
        f"- PPTX: `{summary['artifacts']['pptx']}`",
        f"- Comparison HTML: `{summary['artifacts']['comparison_html']}`",
        "",
        "## Checks",
        "",
        f"- Visual strategy warnings: `{summary['visual_strategy']['warning_count']}`",
        f"- Text fit warnings: `{summary['text_fit']['warning_count']}`",
        f"- Render status: `{summary['render']['status']}`",
        "",
        "## Editability",
        "",
    ]
    for key, value in summary.get("editability", {}).items():
        lines.append(f"- {key}: `{value}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_qa(
    plan_path: Path,
    *,
    source_path: Path | None,
    out_dir: Path,
    output_pptx: Path | None,
    skip_render: bool,
    require_strategy_review: bool,
    continue_on_warnings: bool,
    pptx_deps: Path | None,
) -> dict[str, Any]:
    plan_path = plan_path.resolve()
    if source_path is not None:
        source_path = source_path.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pptx_path = (output_pptx.resolve() if output_pptx else out_dir / "editable-output.pptx")
    visual_report = out_dir / "visual_strategy_report.json"
    text_fit_report = out_dir / "text_fit_report.json"
    packaging_report = out_dir / "packaging_report.json"
    editability_report = out_dir / "editability_report.json"
    render_report = out_dir / "render_report.json"
    render_dir = out_dir / "render"
    comparison_html = out_dir / "visual-qa-comparison.html"
    summary_json = out_dir / "qa_summary.json"
    summary_md = out_dir / "qa_summary.md"

    steps: list[dict[str, Any]] = []
    visual_cmd = python_cmd(
        "check_reconstruction_visual_strategy.py",
        str(plan_path),
        "--out",
        str(visual_report),
    )
    if require_strategy_review:
        visual_cmd.append("--require-strategy-review")
    steps.append(run_step("visual_strategy", visual_cmd, allow_warning_exit=continue_on_warnings))

    steps.append(
        run_step(
            "text_fit",
            python_cmd("check_reconstruction_plan_text_fit.py", str(plan_path), "--out", str(text_fit_report)),
            allow_warning_exit=continue_on_warnings,
        )
    )

    package_cmd = python_cmd(
        "package_reconstruction_deck.py",
        str(plan_path),
        "--out",
        str(pptx_path),
        "--report",
        str(packaging_report),
    )
    if pptx_deps is not None:
        package_cmd.extend(["--pptx-deps", str(pptx_deps)])
    steps.append(run_step("package", package_cmd))

    steps.append(
        run_step(
            "inspect_editability",
            python_cmd("inspect_pptx_editability.py", str(pptx_path), "--out", str(editability_report)),
        )
    )

    render_status = "skipped"
    render_image = render_dir / "slide_01.png"
    if not skip_render:
        render_cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT_DIR / "render_pptx_qa.ps1"),
            "-Pptx",
            str(pptx_path),
            "-OutDir",
            powershell_join_path_arg(render_dir),
            "-Report",
            powershell_join_path_arg(render_report),
        ]
        if source_path:
            render_cmd.extend(["-Source", str(source_path)])
        steps.append(run_step("powerpoint_render", render_cmd))
        if render_report.exists():
            render_status = str(load_json(render_report).get("status", "unknown"))

    visual = load_json(visual_report)
    text_fit = load_json(text_fit_report)
    packaging = load_json(packaging_report)
    editability = load_json(editability_report)
    total_warnings = warning_count(visual) + warning_count(text_fit)
    status = "pass" if total_warnings == 0 and render_status in {"skipped", "rendered"} else "warnings"

    summary = {
        "status": status,
        "plan": str(plan_path),
        "source": str(source_path) if source_path else None,
        "steps": steps,
        "total_warning_count": total_warnings,
        "visual_strategy": {"status": visual.get("status"), **visual.get("summary", {})},
        "text_fit": {"status": text_fit.get("status"), **text_fit.get("summary", {})},
        "packaging": packaging.get("summary", {}),
        "editability": editability.get("summary", {}),
        "render": {"status": render_status},
        "artifacts": {
            "pptx": str(pptx_path),
            "visual_strategy_report": str(visual_report),
            "text_fit_report": str(text_fit_report),
            "packaging_report": str(packaging_report),
            "editability_report": str(editability_report),
            "render_report": str(render_report) if render_report.exists() else None,
            "comparison_html": str(comparison_html),
            "qa_summary_md": str(summary_md),
        },
    }
    write_json(summary_json, summary)
    write_markdown_summary(summary_md, summary)
    make_html(
        comparison_html,
        title=f"Reconstruction QA - {plan_path.name}",
        source_path=source_path,
        render_image=render_image if render_image.exists() else None,
        summary=summary,
    )
    return {"status": status, "summary": summary, "artifacts": summary["artifacts"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run standard reconstruction QA for a reviewed source_reconstruction_plan.json.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--source", type=Path, help="Original source image for the comparison HTML and render QA.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--output-pptx", type=Path)
    parser.add_argument("--skip-render", action="store_true", help="Skip PowerPoint render QA.")
    parser.add_argument("--require-strategy-review", action="store_true")
    parser.add_argument("--continue-on-warnings", action="store_true")
    parser.add_argument("--pptx-deps", type=Path, default=Path("_no_pptx_deps"))
    args = parser.parse_args()

    try:
        result = run_qa(
            args.plan,
            source_path=args.source,
            out_dir=args.out_dir,
            output_pptx=args.output_pptx,
            skip_render=args.skip_render,
            require_strategy_review=args.require_strategy_review,
            continue_on_warnings=args.continue_on_warnings,
            pptx_deps=args.pptx_deps,
        )
    except StepFailed as exc:
        payload = {
            "status": "failed",
            "step": exc.name,
            "returncode": exc.returncode,
            "command": exc.command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(exc.returncode)

    print(json.dumps({"status": result["status"], "artifacts": result["artifacts"]}, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "pass" else 2)


if __name__ == "__main__":
    main()
