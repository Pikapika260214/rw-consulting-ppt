param(
  [Parameter(Mandatory = $true)][string]$DeckPath,
  [Parameter(Mandatory = $true)][string]$OutputDirectory,
  [int]$MaxPixels = 1600
)

$ErrorActionPreference = 'Stop'
$resolvedDeck = (Resolve-Path -LiteralPath $DeckPath).Path
$resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
if ($MaxPixels -le 0) { throw 'MaxPixels must be positive.' }
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

function Get-ExportSize {
  param([double]$Width, [double]$Height, [int]$LongestSide)
  if ($Width -le 0 -or $Height -le 0) { throw 'PowerPoint returned an invalid slide size.' }
  if ($Width -ge $Height) {
    $outWidth = $LongestSide
    $outHeight = [math]::Max(1, [int][math]::Round($LongestSide * $Height / $Width))
  } else {
    $outHeight = $LongestSide
    $outWidth = [math]::Max(1, [int][math]::Round($LongestSide * $Width / $Height))
  }
  return [pscustomobject]@{ width = $outWidth; height = $outHeight }
}

$powerPoint = $null
$presentation = $null
try {
  $powerPoint = New-Object -ComObject PowerPoint.Application
  # Open read-only and without a window.  Only this presentation is closed in
  # finally; the host application is never asked to terminate.
  $presentation = $powerPoint.Presentations.Open($resolvedDeck, $true, $false, $false)
  $slideWidth = [double]$presentation.PageSetup.SlideWidth
  $slideHeight = [double]$presentation.PageSetup.SlideHeight
  $exportSize = Get-ExportSize $slideWidth $slideHeight $MaxPixels
  $slideRecords = @()
  for ($i = 1; $i -le $presentation.Slides.Count; $i++) {
    $slide = $presentation.Slides.Item($i)
    $target = Join-Path $resolvedOutput ('page-{0:00}.png' -f $i)
    $slide.Export($target, 'PNG', $exportSize.width, $exportSize.height)
    $types = @()
    for ($j = 1; $j -le $slide.Shapes.Count; $j++) {
      $types += [int]$slide.Shapes.Item($j).Type
    }
    $slideRecords += [pscustomobject]@{
      page = $i
      shapeCount = $slide.Shapes.Count
      shapeTypes = $types
      export = [pscustomobject]@{ width = $exportSize.width; height = $exportSize.height }
    }
  }
  [pscustomobject]@{
    deck = $resolvedDeck
    openedInPowerPoint = $true
    slideCount = $presentation.Slides.Count
    slideWidth = $slideWidth
    slideHeight = $slideHeight
    exportSizePx = [pscustomobject]@{ width = $exportSize.width; height = $exportSize.height }
    slides = $slideRecords
    exportedAt = (Get-Date).ToString('o')
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $resolvedOutput 'powerpoint-verification.json') -Encoding utf8
} finally {
  if ($null -ne $presentation) {
    try { $presentation.Close() } catch {}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
  }
  if ($null -ne $powerPoint) {
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
  }
}
