# Reconstruction QA

Use this reference before accepting any reconstruction or mixed reconstruction output.

## Hard Gates

Reject and revise when:

- `fullSlidePictures > 0` and the user did not explicitly accept a full-slide fallback.
- Meaningful source text remains inside a picture while editable text is overlaid above it.
- The PPTX has no native reconstruction evidence for structured pages.
- Multiline semantic text is split into many unrelated text boxes.
- Body, callout, or panel text has been shrunk into tiny font-size outliers compared with the source role.
- Editable text is made readable by invented pale rectangles, generic backing fills, or non-source-matched text background blocks.
- Textless crop cleanup erased or damaged non-text visual anchors such as arrows, arrowheads, route lines, connectors, step markers, card edges, cut corners, dividers, or icons.
- `text_fit_report.json` has unresolved `text_overflow_risk`, `punctuation_orphan_line`, or `single_character_line` warnings.
- `text_fit_report.json` has unresolved `candidate_multiline_split` warnings for same-style adjacent text that should be one semantic multiline text box.
- `visual_strategy_report.json` has unresolved `native_redraw_used_for_high_risk_region`, `expected_textless_crop_missing`, or `textless_crop_text_overlay_missing` warnings.
- PowerPoint cannot open or render the generated PPTX.
- Visual QA is skipped.

## Required Checks

Run these checks for every quality output:

Default one-command flow:

```powershell
python scripts/run_reconstruction_qa.py path\to\source_reconstruction_plan.json --source path\to\source.png --out-dir path\to\qa --require-strategy-review
```

This writes `visual_strategy_report.json`, `text_fit_report.json`, `packaging_report.json`, `editability_report.json`, `render_report.json`, `qa_summary.json`, `qa_summary.md`, and `visual-qa-comparison.html`.

Use the separate commands only when debugging a specific stage:

```powershell
python scripts/check_reconstruction_visual_strategy.py path\to\source_reconstruction_plan.json --out path\to\visual_strategy_report.json --require-strategy-review
python scripts/check_reconstruction_plan_text_fit.py path\to\source_reconstruction_plan.json --out path\to\text_fit_report.json
python scripts/package_reconstruction_deck.py path\to\source_reconstruction_plan.json --out path\to\editable.pptx --report path\to\packaging_report.json
python scripts/inspect_pptx_editability.py path\to\editable.pptx --out path\to\editability_report.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\render_pptx_qa.ps1 -Pptx path\to\editable.pptx -OutDir path\to\render -Source path\to\source.png -Report path\to\render_report.json
```

## Structure Metrics

Review these fields:

- `pictures`
- `fullSlidePictures`
- `nativeShapes`
- `nativeLines`
- `nativeDashedLines`
- `nativeTables`
- `editableTextBodies`
- `mergedMultilineBlocks`
- `splitTextBoxesPrevented`
- `unwantedSplitTextBoxes`
- `text_fit_report.summary.warnings_by_type.candidate_multiline_split`
- `noAutofitTextBodies`
- `visual_strategy_report.summary.regions`

Good reconstruction does not mean maximum native object count. Complex visual modules may remain tight source crops when native redraw would drift.

For bridge/risk pages, judge the crop boundary rather than the native shape count alone. A low `nativeShapes` count can pass when `fullSlidePictures=0`, crops are bounded to semantic modules, all meaningful text is editable, and the strategy review records why native redraw would drift.

## Visual Review

Compare the source image and rendered PNG. Specifically check:

- no obvious source text residue;
- no duplicated source/editable text;
- no missing icon strokes;
- no crop boxes that include nearby text;
- no visible patch squares from preserved source backgrounds;
- no native shape drift for arrows, badges, bars, or process cards;
- no missing arrowheads, broken route lines, erased connectors, missing step markers, clipped icons, or missing card edges after textless crop cleanup;
- no template-like native redraw for curved connectors, bracket arrows, side path modules, or icon-connected navigation paths;
- no complex artwork region redrawn natively when a crop would preserve the source better;
- no body/callout text that is visibly too small relative to the source;
- no invented text backing rectangles or pale fills behind editable text;
- no bridge/risk module rebuilt as a heavy native template when a bounded textless crop would preserve the original better;
- no one-character wrap or text overflow;
- no punctuation left alone on a separate line;
- no full-slide crop used where semantic local crops would work;
- no large crop that swallows unrelated regions.

## Accepted Tradeoffs

These are acceptable when recorded in limitations:

- complex icons as source crops;
- gradient or arrow-ended bars as textless crops;
- complex process-card groups as local textless crops;
- complex connector and side-path modules as local textless crops with editable text overlaid;
- bridge/risk modules split into bounded local textless crops such as main bridge, risk row, and takeaway strip;
- lower native shape count when fidelity improves;
- semantic multiline text in one text box rather than line-level trace.
