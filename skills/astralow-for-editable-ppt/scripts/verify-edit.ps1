param(
  [Parameter(Mandatory = $true)][string]$DeckPath,
  [Parameter(Mandatory = $true)][string]$OutputDirectory,
  [Parameter(Mandatory = $true)][string]$EditsPath
)

$ErrorActionPreference = 'Stop'
$resolvedDeck = (Resolve-Path -LiteralPath $DeckPath).Path
$resolvedEdits = (Resolve-Path -LiteralPath $EditsPath).Path
$resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

$runDirectory = Join-Path $resolvedOutput ('run-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $runDirectory | Out-Null
$copyPath = Join-Path $runDirectory 'edited-copy.pptx'
$resultPath = Join-Path $resolvedOutput 'real-edit-verification.json'
$sourceHashBefore = (Get-FileHash -LiteralPath $resolvedDeck -Algorithm SHA256).Hash

$powerPoint = $null
$presentation = $null
$reopened = $null
$rules = @()
$edits = @()
$objects = @()
$expectedByPath = @{}
$matchedRules = @()
$reopenedTexts = @{}
$exitCode = 0
$errorMessage = $null
$sourceUnchanged = $false

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

function Read-Rules {
  $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedEdits | ConvertFrom-Json
  $items = @($raw)
  if ($items.Count -eq 0) { throw 'EditsPath must contain a non-empty JSON array.' }
  $index = 0
  foreach ($item in $items) {
    if ($null -eq $item -or $null -eq $item.old -or $null -eq $item.new) {
      throw "Edit rule $index must contain old and new strings."
    }
    $old = [string]$item.old
    $new = [string]$item.new
    if ([string]::IsNullOrWhiteSpace($old) -or [string]::IsNullOrWhiteSpace($new)) {
      throw "Edit rule $index cannot have an empty old or new value."
    }
    if ($old -ceq $new) { throw "Edit rule $index has identical old and new values." }
    [pscustomobject]@{ old = $old; new = $new; index = $index }
    $index++
  }
}

function Capture-Font {
  param($Range)
  $state = [ordered]@{}
  try { $state.Name = [string]$Range.Font.Name } catch {}
  try { $state.Size = [double]$Range.Font.Size } catch {}
  try { $state.Bold = [int]$Range.Font.Bold } catch {}
  try { $state.Italic = [int]$Range.Font.Italic } catch {}
  try { $state.Underline = [int]$Range.Font.Underline } catch {}
  try { $state.Rgb = [int]$Range.Font.Color.RGB } catch {}
  return $state
}

function Restore-Font {
  param($Range, $State)
  if ($State.Contains('Name')) { try { $Range.Font.Name = $State.Name } catch {} }
  if ($State.Contains('Size')) { try { $Range.Font.Size = $State.Size } catch {} }
  if ($State.Contains('Bold')) { try { $Range.Font.Bold = $State.Bold } catch {} }
  if ($State.Contains('Italic')) { try { $Range.Font.Italic = $State.Italic } catch {} }
  if ($State.Contains('Underline')) { try { $Range.Font.Underline = $State.Underline } catch {} }
  if ($State.Contains('Rgb')) { try { $Range.Font.Color.RGB = $State.Rgb } catch {} }
}

function Visit-Shape {
  param($Shape, [string]$ObjectPath, [scriptblock]$TextCallback)
  $shapeType = [int]$Shape.Type
  try {
    if ([int]$Shape.HasTextFrame -ne 0) {
      & $TextCallback $Shape $ObjectPath
    }
  } catch {}

  if ($shapeType -eq 6) {
    for ($k = 1; $k -le $Shape.GroupItems.Count; $k++) {
      Visit-Shape $Shape.GroupItems.Item($k) "$ObjectPath/group:$k" $TextCallback
    }
  }
  try {
    if ([int]$Shape.HasTable -ne 0) {
      for ($r = 1; $r -le $Shape.Table.Rows.Count; $r++) {
        for ($c = 1; $c -le $Shape.Table.Columns.Count; $c++) {
          $cellShape = $Shape.Table.Cell($r, $c).Shape
          Visit-Shape $cellShape "$ObjectPath/cell:$r,$c" $TextCallback
        }
      }
    }
  } catch {}
}

function Visit-Presentation {
  param($Presentation, [scriptblock]$TextCallback)
  for ($i = 1; $i -le $Presentation.Slides.Count; $i++) {
    $slide = $Presentation.Slides.Item($i)
    for ($j = 1; $j -le $slide.Shapes.Count; $j++) {
      Visit-Shape $slide.Shapes.Item($j) "slide:$i/shape:$j" $TextCallback
    }
  }
}

function Record-Object {
  param($Shape, [string]$ObjectPath)
  $text = ''
  try { if ([int]$Shape.HasTextFrame -ne 0) { $text = [string]$Shape.TextFrame.TextRange.Text } } catch {}
  $script:objects += [pscustomobject]@{
    path = $ObjectPath
    name = [string]$Shape.Name
    type = [int]$Shape.Type
    textBefore = $text
  }
}

function Try-Edit-Shape {
  param($Shape, [string]$ObjectPath)
  if ($script:ruleFound -contains $true -and ($script:ruleFound | Where-Object { $_ -eq $false }).Count -eq 0) {
    return
  }
  $range = $null
  try {
    if ([int]$Shape.HasTextFrame -eq 0) { return }
    $range = $Shape.TextFrame.TextRange
  } catch { return }
  $text = [string]$range.Text
  for ($index = 0; $index -lt $script:rules.Count; $index++) {
    if ($script:ruleFound[$index]) { continue }
    $rule = $script:rules[$index]
    $start = $text.IndexOf($rule.old, [StringComparison]::Ordinal)
    if ($start -lt 0) { continue }
    $oldRange = $range.Characters($start + 1, $rule.old.Length)
    $fontState = Capture-Font $oldRange
    $oldFullText = $text
    # Characters() edits only the selected text and retains its object identity.
    $oldRange.Text = $rule.new
    $updatedRange = $Shape.TextFrame.TextRange
    $newFullText = [string]$updatedRange.Text
    $newRange = $updatedRange.Characters($start + 1, $rule.new.Length)
    Restore-Font $newRange $fontState
    $script:ruleFound[$index] = $true
    $script:expectedByPath[$ObjectPath] = $newFullText
    $script:edits += [pscustomobject]@{
      ruleIndex = $index
      objectPath = $ObjectPath
      objectName = [string]$Shape.Name
      before = $rule.old
      after = $rule.new
      fullTextBefore = $oldFullText
      fullTextAfterThisRule = $newFullText
    }
    $text = $newFullText
    $range = $Shape.TextFrame.TextRange
  }
}

function Collect-Reopened-Text {
  param($Shape, [string]$ObjectPath)
  try {
    if ([int]$Shape.HasTextFrame -ne 0) {
      $script:reopenedTexts[$ObjectPath] = [string]$Shape.TextFrame.TextRange.Text
    }
  } catch {}
}

$result = [ordered]@{
  source = $resolvedDeck
  editsPath = $resolvedEdits
  outputDirectory = $resolvedOutput
  runDirectory = $runDirectory
  editedCopy = $copyPath
  reopenedInPowerPoint = $false
  passed = $false
  sourceUnchanged = $false
  rules = @()
  changes = @()
  objects = @()
  objectChecks = @()
  error = $null
  testedAt = $null
}

try {
  $rules = @(Read-Rules)
  $result.rules = $rules
  $matchedRules = @($false) * $rules.Count
  Copy-Item -LiteralPath $resolvedDeck -Destination $copyPath
  $powerPoint = New-Object -ComObject PowerPoint.Application
  $presentation = $powerPoint.Presentations.Open($copyPath, $false, $false, $false)
  Visit-Presentation $presentation ${function:Record-Object}
  $script:rules = $rules
  $script:ruleFound = $matchedRules
  Visit-Presentation $presentation ${function:Try-Edit-Shape}
  $matchedRules = @($script:ruleFound)
  $presentation.Save()
  $presentation.Close()
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
  $presentation = $null

  $reopened = $powerPoint.Presentations.Open($copyPath, $true, $false, $false)
  $result.reopenedInPowerPoint = $true
  Visit-Presentation $reopened ${function:Collect-Reopened-Text}
  $objectChecks = @()
  foreach ($path in $expectedByPath.Keys) {
    $expected = [string]$expectedByPath[$path]
    $found = $reopenedTexts.ContainsKey($path)
    $actual = if ($found) { [string]$reopenedTexts[$path] } else { $null }
    $objectChecks += [pscustomobject]@{
      objectPath = $path
      expectedFullText = $expected
      actualFullText = $actual
      matched = ($found -and $actual -ceq $expected)
    }
  }
  $missingRules = @()
  for ($i = 0; $i -lt $rules.Count; $i++) {
    if (-not $matchedRules[$i]) { $missingRules += $i }
  }
  foreach ($edit in $edits) {
    $edit | Add-Member -NotePropertyName expectedFinalText -NotePropertyValue ([string]$expectedByPath[$edit.objectPath]) -Force
  }
  $badObjects = @($objectChecks | Where-Object { -not $_.matched })
  if ($missingRules.Count -gt 0) {
    throw ('At least one occurrence was not found for rule index: ' + ($missingRules -join ', '))
  }
  if ($badObjects.Count -gt 0) {
    throw ('Reopened object text did not match expected text for: ' + (($badObjects | ForEach-Object { $_.objectPath }) -join ', '))
  }
  if ($edits.Count -ne $rules.Count) {
    throw 'The verifier expected exactly one successful replacement per rule.'
  }
  $result.passed = $true
} catch {
  $exitCode = 1
  $errorMessage = $_.Exception.Message
  $result.error = $errorMessage
} finally {
  if ($null -ne $reopened) {
    try { $reopened.Close() } catch {}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($reopened)
    $reopened = $null
  }
  if ($null -ne $presentation) {
    try { $presentation.Close() } catch {}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    $presentation = $null
  }
  if ($null -ne $powerPoint) {
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    $powerPoint = $null
  }
  try {
    $sourceHashAfter = (Get-FileHash -LiteralPath $resolvedDeck -Algorithm SHA256).Hash
    $sourceUnchanged = ($sourceHashBefore -ceq $sourceHashAfter)
  } catch {
    $sourceUnchanged = $false
  }
  $result.sourceUnchanged = $sourceUnchanged
  $result.rules = @($rules)
  $result.changes = @($edits)
  $result.objects = @($objects)
  $result.objectChecks = @($objectChecks)
  $result.testedAt = (Get-Date).ToString('o')
  if (-not $sourceUnchanged) {
    $result.passed = $false
    if ([string]::IsNullOrWhiteSpace($result.error)) { $result.error = 'Source PPTX hash changed.' }
    $exitCode = 1
  }
  $json = $result | ConvertTo-Json -Depth 20
  Set-Content -LiteralPath $resultPath -Value $json -Encoding utf8
  Write-Output $json
}

if ($exitCode -ne 0 -or -not $result.passed) { exit 1 }
