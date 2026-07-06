param(
  [Parameter(Mandatory = $true)]
  [string]$Pptx,

  [Parameter(Mandatory = $true)]
  [string]$OutDir,

  [Parameter(Mandatory = $false)]
  [string]$Report,

  [Parameter(Mandatory = $false)]
  [string]$Source,

  [Parameter(Mandatory = $false)]
  [int]$Dpi = 150
)

$ErrorActionPreference = "Stop"

function Resolve-InputPath {
  param([string]$PathValue)
  return (Resolve-Path -LiteralPath $PathValue).Path
}

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

$pptxPath = Resolve-InputPath $Pptx
$outPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutDir))
$reportPath = if ($Report) {
  [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Report))
} else {
  Join-Path $outPath "render_report.json"
}
$sourcePath = if ($Source) { Resolve-InputPath $Source } else { $null }

$reportObject = [ordered]@{
  status = "unknown"
  date = (Get-Date -Format "yyyy-MM-dd")
  pptx = $pptxPath
  out_dir = $outPath
  source_image = $sourcePath
  renderer = "powerpoint"
  backend = "powershell-com"
  dpi = $Dpi
}

$app = $null
$presentation = $null

try {
  New-Item -ItemType Directory -Force -Path $outPath | Out-Null
  New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($reportPath)) | Out-Null

  $app = New-Object -ComObject PowerPoint.Application
  try { $app.Visible = $true } catch {}

  $reportObject.powerpoint_version = [string]$app.Version

  # Open(FileName, ReadOnly, Untitled, WithWindow)
  # PowerPoint COM can reject image-heavy python-pptx files when opened
  # headlessly in some local Office states. Windowed open is more reliable
  # for QA export and the app is still closed in finally.
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
[System.IO.File]::WriteAllText($reportPath, $json + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
@{ status = $reportObject.status; report = $reportPath } | ConvertTo-Json -Compress

if ($reportObject.status -eq "rendered") {
  exit 0
}
exit 1
