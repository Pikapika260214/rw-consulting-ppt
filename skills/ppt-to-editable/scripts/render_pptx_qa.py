#!/usr/bin/env python
"""Render a PPTX to PNG for deterministic visual QA.

The helper standardizes render outputs for per-slide workers:

- `status=rendered` only when a PNG exists and can be inspected.
- `status=renderer-unavailable` when no supported renderer is available.
- `status=error` when rendering was attempted but failed.

Workers can pass `--existing-rendered` when a renderer already exported a PNG;
the helper still writes the canonical `rendered.png` and `render_report.json`.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def image_diff_metrics(source: Path, rendered: Path) -> dict[str, Any]:
    with Image.open(source).convert("RGB") as src, Image.open(rendered).convert("RGB") as rnd:
        rendered_original_size = list(rnd.size)
        if rnd.size != src.size:
            rnd = rnd.resize(src.size)
        diff = ImageChops.difference(src, rnd)
        stat = ImageStat.Stat(diff)
        mean_abs = sum(stat.mean) / len(stat.mean)
        extrema = diff.getextrema()
        max_abs = max(channel[1] for channel in extrema)
        return {
            "source_png": str(source.resolve()),
            "rendered_png": str(rendered.resolve()),
            "source_size": list(src.size),
            "rendered_original_size": rendered_original_size,
            "compared_size": list(src.size),
            "mean_abs_rgb_diff_0_255": round(mean_abs, 2),
            "max_abs_rgb_diff_0_255": int(max_abs),
            "note": "Pixel diff is indicative only; editable reconstruction is not expected to be a raster clone.",
        }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_rendered_png_from_existing(existing: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stable = out_dir / "rendered.png"
    shutil.copy2(existing, stable)
    return stable


def powershell_script_text() -> str:
    return r'''
param(
  [Parameter(Mandatory = $true)]
  [string]$Pptx,

  [Parameter(Mandatory = $true)]
  [string]$OutDir,

  [Parameter(Mandatory = $true)]
  [string]$RawReport,

  [Parameter(Mandatory = $false)]
  [int]$Dpi = 150
)

$ErrorActionPreference = "Stop"

function Release-ComObject {
  param($Object)
  if ($null -ne $Object) {
    try {
      [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Object)
    } catch {
      try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($Object) } catch {}
    }
  }
}

$pptxPath = (Resolve-Path -LiteralPath $Pptx).Path
$outPath = [System.IO.Path]::GetFullPath($OutDir)
$rawReportPath = [System.IO.Path]::GetFullPath($RawReport)

$reportObject = [ordered]@{
  status = "unknown"
  pptx = $pptxPath
  out_dir = $outPath
  renderer = "powerpoint"
  backend = "powershell-com"
  dpi = $Dpi
}

$app = $null
$presentation = $null

try {
  New-Item -ItemType Directory -Force -Path $outPath | Out-Null
  New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($rawReportPath)) | Out-Null

  $app = New-Object -ComObject PowerPoint.Application
  try { $app.Visible = $true } catch {}
  $reportObject.powerpoint_version = [string]$app.Version

  $presentation = $app.Presentations.Open($pptxPath, -1, 0, -1)

  $slideWidthPt = [double]$presentation.PageSetup.SlideWidth
  $slideHeightPt = [double]$presentation.PageSetup.SlideHeight
  $pxW = [Math]::Max(1, [int][Math]::Round($slideWidthPt / 72.0 * $Dpi))
  $pxH = [Math]::Max(1, [int][Math]::Round($slideHeightPt / 72.0 * $Dpi))
  $slideCount = [int]$presentation.Slides.Count

  $slides = @()
  for ($i = 1; $i -le $slideCount; $i++) {
    $target = Join-Path $outPath ("slide_{0:D2}.png" -f $i)
    $slide = $presentation.Slides.Item($i)
    $slide.Export($target, "PNG", $pxW, $pxH)
    $item = Get-Item -LiteralPath $target -ErrorAction SilentlyContinue
    $slides += [ordered]@{
      index = $i
      png = $target
      exists = [bool]$item
      bytes = if ($item) { [int64]$item.Length } else { 0 }
    }
    Release-ComObject $slide
  }

  $rendered = @($slides | Where-Object { $_.exists -and $_.bytes -gt 0 })
  $reportObject.status = if ($rendered.Count -gt 0) { "rendered" } else { "error" }
  if ($rendered.Count -eq 0) {
    $reportObject.error = "PowerPoint reported success but no PNG was written."
  }
  $reportObject.slide_px = @($pxW, $pxH)
  $reportObject.slide_count = $slideCount
  $reportObject.slides = $slides
} catch {
  $reportObject.status = "error"
  $reportObject.error = $_.Exception.Message
} finally {
  if ($null -ne $presentation) {
    try { $presentation.Close() } catch {}
  }
  if ($null -ne $app) {
    try { $app.Quit() } catch {}
  }
  Release-ComObject $presentation
  Release-ComObject $app
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}

$json = $reportObject | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($rawReportPath, $json + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
$json

if ($reportObject.status -eq "rendered") {
  exit 0
}
exit 1
'''


def run_powerpoint_render(pptx: Path, out_dir: Path, report_dir: Path, dpi: int, timeout: int) -> dict[str, Any]:
    if platform.system().lower() != "windows":
        return {
            "status": "renderer-unavailable",
            "renderer": "powerpoint",
            "error": "PowerPoint COM render is only supported on Windows.",
        }

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        return {
            "status": "renderer-unavailable",
            "renderer": "powerpoint",
            "error": "PowerShell executable not found.",
        }

    report_dir.mkdir(parents=True, exist_ok=True)
    script_path = report_dir / "render_powerpoint_com.ps1"
    raw_report = report_dir / "powerpoint_render_raw.json"
    script_path.write_text(powershell_script_text(), encoding="utf-8")
    cmd = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-Pptx",
        str(pptx),
        "-OutDir",
        str(out_dir),
        "-RawReport",
        str(raw_report),
        "-Dpi",
        str(dpi),
    ]
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "error",
            "renderer": "powerpoint",
            "backend": "powershell-com",
            "error": f"powerpoint_render_timeout_after_{timeout}s",
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "command": cmd,
        }

    raw: dict[str, Any] = {}
    if raw_report.exists():
        try:
            raw = json.loads(raw_report.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            raw = {}

    elapsed = round(time.perf_counter() - started, 3)
    status = raw.get("status")
    if proc.returncode != 0 and not status:
        error_text = proc.stderr.strip() or proc.stdout.strip()
        unavailable_markers = [
            "Cannot create ActiveX component",
            "New-Object",
            "COM",
            "Retrieving the COM class factory",
        ]
        status = "renderer-unavailable" if any(marker in error_text for marker in unavailable_markers) else "error"
        raw = {"error": error_text}

    raw["status"] = status or ("rendered" if proc.returncode == 0 else "error")
    raw["elapsed_seconds"] = elapsed
    raw["command"] = cmd
    raw["stdout"] = proc.stdout.strip()
    raw["stderr"] = proc.stderr.strip()
    return raw


def first_rendered_png(raw: dict[str, Any], out_dir: Path) -> Path | None:
    slides = raw.get("slides")
    if isinstance(slides, list):
        for slide in slides:
            if isinstance(slide, dict) and slide.get("exists") and int(slide.get("bytes") or 0) > 0:
                path = Path(str(slide.get("png")))
                if path.exists():
                    return path
    for pattern in ("slide_01.png", "幻灯片1.PNG", "*.png", "*.PNG"):
        matches = sorted(out_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def build_report(
    pptx: Path,
    out_dir: Path,
    report_path: Path,
    source: Path | None,
    renderer: str,
    rendered_png: Path | None,
    raw: dict[str, Any],
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "ppt-to-editable-render-qa-v1",
        "status": "rendered" if rendered_png and rendered_png.exists() else raw.get("status", "error"),
        "renderer": renderer,
        "pptx": str(pptx.resolve()),
        "out_dir": str(out_dir.resolve()),
        "report": str(report_path.resolve()),
        "rendered_png": str(rendered_png.resolve()) if rendered_png and rendered_png.exists() else None,
        "source_image": str(source.resolve()) if source else None,
        "raw": raw,
    }
    if source and rendered_png and source.exists() and rendered_png.exists():
        report["diff_metrics"] = image_diff_metrics(source, rendered_png)
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PPTX to PNG for visual QA")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--existing-rendered", type=Path, default=None)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    configure_stdout()
    args = parse_args(argv)
    pptx = args.pptx.resolve()
    out_dir = args.out_dir.resolve()
    report_path = (args.report or (out_dir / "render_report.json")).resolve()
    source = args.source.resolve() if args.source else None

    out_dir.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any]
    renderer: str
    rendered_png: Path | None

    if args.existing_rendered:
        existing = args.existing_rendered.resolve()
        if not existing.exists():
            raw = {"status": "error", "error": f"existing_rendered_not_found: {existing}"}
            renderer = "existing-rendered-png"
            rendered_png = None
        else:
            rendered_png = stable_rendered_png_from_existing(existing, out_dir)
            renderer = "existing-rendered-png"
            raw = {
                "status": "rendered",
                "existing_rendered": str(existing),
                "stable_rendered": str(rendered_png),
            }
    else:
        renderer = "powerpoint"
        raw = run_powerpoint_render(pptx, out_dir, report_path.parent, args.dpi, args.timeout)
        rendered_png = first_rendered_png(raw, out_dir) if raw.get("status") == "rendered" else None
        if rendered_png and rendered_png.name != "rendered.png":
            stable = out_dir / "rendered.png"
            shutil.copy2(rendered_png, stable)
            rendered_png = stable

    report = build_report(pptx, out_dir, report_path, source, renderer, rendered_png, raw)
    write_json(report_path, report)
    print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False))
    return 0 if report["status"] == "rendered" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
